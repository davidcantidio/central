import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from common.models import DeliveryControlCreative, DeliveryControlRedesSociais, Client, Users, CategoryEnumCreative, CategoryEnumRedesSociais
from common.database import engine
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import streamlit as st
from dateutil.relativedelta import relativedelta
import logging
from functools import wraps

# Configura o log
logging.basicConfig(filename='process_xlsx.log', level=logging.INFO)

# Crie uma sessão
Session = sessionmaker(bind=engine)

# Definição do decorator with_db_session
def with_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = Session()
        try:
            result = func(*args, session=session, **kwargs)
            session.commit()
            return result
        except Exception as e:
            logging.error(f"Erro na função '{func.__name__}': {e}", exc_info=True)
            session.rollback()
            raise e
        finally:
            session.close()
    return wrapper

def initialize_session_state():
    if 'unmatched_clients' not in st.session_state:
        st.session_state.unmatched_clients = []
    if 'client_name_map' not in st.session_state:
        st.session_state.client_name_map = {}
    if 'clients_to_add' not in st.session_state:
        st.session_state.clients_to_add = []
    if 'actions_taken' not in st.session_state:
        st.session_state.actions_taken = []
    if 'unmatched_categories' not in st.session_state:
        st.session_state.unmatched_categories = []
    if 'job_category_map' not in st.session_state:
        st.session_state.job_category_map = {}
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'session' not in st.session_state:
        st.session_state.session = None

# Call initialize_session_state at the start
initialize_session_state()

def extract_mandalecas(title):
    match = re.search(r'mdl\s?(\d+[.,]?\d*)', title, re.IGNORECASE)
    if match:
        mandalecas = match.group(1).replace(',', '.')
        return float(mandalecas)
    return None

def identificar_categoria(titulo, projeto):
    titulo_lower = str(titulo).lower()
    categorias_encontradas = set()

    if "adaptação" in titulo_lower:
        categorias_encontradas.add("Adaptação")
    if "criação" in titulo_lower:
        categorias_encontradas.add("Criação")
    if any(keyword in titulo_lower for keyword in ["story", "stories", "storie"]):
        categorias_encontradas.add("Stories")
    if any(keyword in titulo_lower for keyword in ["reel", "reels"]):
        categorias_encontradas.add("Reels")
    if any(keyword in titulo_lower for keyword in ["card", "cards"]):
        categorias_encontradas.add("Cards")

    if len(categorias_encontradas) == 1:
        return categorias_encontradas.pop()
    else:
        return None

def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

def calcular_e_atualizar_mandalecas_acumuladas(client, session):
    job_mais_antigo = session.query(DeliveryControlCreative).filter_by(client_id=client.id).order_by(DeliveryControlCreative.job_creation_date).first()
    if not job_mais_antigo:
        return
    
    data_mais_antiga = job_mais_antigo.job_creation_date
    data_atual = datetime.now()
    numero_meses = relativedelta(data_atual, data_mais_antiga).years * 12 + relativedelta(data_atual, data_mais_antiga).months + 1
    
    mandalecas_contratadas_criacao = numero_meses * (client.n_monthly_contracted_creative_mandalecas or 0)
    mandalecas_contratadas_adaptacao = numero_meses * (client.n_monthly_contracted_format_adaptation_mandalecas or 0)
    mandalecas_contratadas_conteudo = numero_meses * (client.n_monthly_contracted_content_mandalecas or 0)
    mandalecas_contratadas_reels = numero_meses * (client.n_monthly_contracted_reels_mandalecas or 0)
    mandalecas_contratadas_stories = numero_meses * (client.n_monthly_contracted_stories_mandalecas or 0)
    mandalecas_contratadas_cards = numero_meses * (client.n_monthly_contracted_cards_mandalecas or 0)
    
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()
    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Criação")
    mandalecas_usadas_adaptacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Adaptação")
    mandalecas_usadas_conteudo = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Conteúdo")
    mandalecas_usadas_reels = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Reels")
    mandalecas_usadas_stories = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Stories")
    mandalecas_usadas_cards = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Cards")
    
    client.accumulated_creative_mandalecas = mandalecas_contratadas_criacao - mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_contratadas_adaptacao - mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_contratadas_conteudo - mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_contratadas_stories - mandalecas_usadas_stories
    client.accumulated_reels_mandalecas = mandalecas_contratadas_reels - mandalecas_usadas_reels
    client.accumulated_cards_mandalecas = mandalecas_contratadas_cards - mandalecas_usadas_cards
    
    session.commit()

def read_excel_file(uploaded_file):
    """
    Lê o arquivo Excel e retorna um DataFrame.

    Parâmetros:
    uploaded_file (UploadedFile): O arquivo Excel carregado pelo usuário.

    Retorna:
    DataFrame: O DataFrame com os dados do arquivo Excel.
    """
    df = pd.read_excel(uploaded_file)
    df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    return df

def match_clients_in_dataframe(df, session):
    """
    Tenta corresponder clientes no DataFrame usando o cache de sessão e o banco de dados.

    Parâmetros:
    df (DataFrame): O DataFrame com os dados do arquivo Excel.
    session (Session): A sessão de banco de dados ativa.

    Retorna:
    tuple: Uma lista de clientes não correspondidos e um mapeamento de nomes de clientes.
    """
    unmatched_clients = []
    client_name_map = {}
    existing_clients = {client.name: client for client in session.query(Client).all()}

    for index, row in df.iterrows():
        client_name = str(row['Cliente'])
        client = existing_clients.get(client_name) or session.query(Client).filter(Client.aliases.contains([client_name])).first()
        if not client:
            unmatched_clients.append((index, client_name))
        else:
            client_name_map[index] = client

    return unmatched_clients, client_name_map

def match_categories_in_dataframe(df, client_name_map):
    """
    Tenta corresponder categorias no DataFrame usando o mapeamento de nomes de clientes.

    Parâmetros:
    df (DataFrame): O DataFrame com os dados do arquivo Excel.
    client_name_map (dict): Mapeamento de nomes de clientes para objetos Client.

    Retorna:
    tuple: Uma lista de categorias não correspondidas e um mapeamento de categorias de trabalho.
    """
    unmatched_categories = []
    job_category_map = {}

    for index, row in df.iterrows():
        categoria = identificar_categoria(row['Título'], row['Projeto'])
        if not categoria:
            unmatched_categories.append((index, row['Título']))
        else:
            job_category_map[index] = categoria

    return unmatched_categories, job_category_map

@with_db_session
def process_xlsx_file(uploaded_file, session):
    initialize_session_state()
    try:
        df = read_excel_file(uploaded_file)
        st.session_state.df = df

        unmatched_clients, client_name_map = match_clients_in_dataframe(df, session)
        unmatched_categories, job_category_map = match_categories_in_dataframe(df, client_name_map)

        st.session_state.unmatched_clients = unmatched_clients
        st.session_state.client_name_map = client_name_map
        st.session_state.unmatched_categories = unmatched_categories
        st.session_state.job_category_map = job_category_map
        st.session_state.session = session  # Armazenar a sessão no estado

        handle_unmatched_entities(unmatched_clients, unmatched_categories, df, client_name_map, job_category_map, session)

    except Exception as e:
        logging.error(f"Erro ao processar dados: {e}", exc_info=True)
        st.error(f"Erro ao processar dados: {e}")

def handle_unmatched_entities(unmatched_clients, unmatched_categories, df, client_name_map, job_category_map, session):
    if unmatched_clients:
        corresponder_clientes()
    elif unmatched_categories:
        match_categories_dialog()
    else:
        process_jobs(df, client_name_map, job_category_map, session)


@with_db_session
def process_jobs(df, client_name_map, job_category_map, session):
    """
    Processa cada linha do DataFrame e atualiza ou insere dados no banco de dados.

    Parâmetros:
    df (DataFrame): O DataFrame com os dados do arquivo Excel.
    client_name_map (dict): Mapeamento de nomes de clientes para objetos Client.
    job_category_map (dict): Mapeamento de categorias de trabalho para índices do DataFrame.
    session (Session): A sessão de banco de dados ativa, gerenciada pelo decorator.
    """
    try:
        for index, row in df.iterrows():
            if index in client_name_map:
                client = client_name_map[index]
                user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
                requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

                doc_num = str(row['Nº Doc']).split('.')[0]
                job_link = f"https://app4.operand.com.br/jobs/{doc_num}"

                mandalecas = extract_mandalecas(row['Título'])
                categoria = job_category_map.get(index)

                doc_id = int(doc_num)

                job_creation_date = convert_to_date(row['Data de criação'])
                job_start_date = convert_to_date(row['Data Início'])
                job_finish_date = convert_to_date(row['Data de Conclusão'])

                project_type = row['Projeto']
                if 'Redes Sociais' in project_type:
                    model = DeliveryControlRedesSociais
                else:
                    model = DeliveryControlCreative

                upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, user_in_charge, requested_by, categoria, project_type, model)

        for client in set(client_name_map.values()):
            calcular_e_atualizar_mandalecas_acumuladas(client, session)
        st.success("Dados processados e inseridos com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao processar trabalhos: {e}", exc_info=True)
        st.error(f"Erro ao processar trabalhos: {e}")

def upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, user_in_charge, requested_by, categoria, project_type, model):
    """
    Insere ou atualiza um registro de controle de entrega no banco de dados.

    Parâmetros:
    session (Session): A sessão de banco de dados ativa.
    doc_id (int): ID do documento.
    client (Client): Objeto Client correspondente.
    row (Series): Linha do DataFrame com os dados do job.
    job_link (str): Link para o job.
    mandalecas (float): Número de mandalecas.
    job_creation_date (date): Data de criação do job.
    job_start_date (date): Data de início do job.
    job_finish_date (date): Data de conclusão do job.
    user_in_charge (Users): Usuário responsável pelo job.
    requested_by (Users): Usuário que requisitou o job.
    categoria (str): Categoria do job.
    project_type (str): Tipo de projeto do job.
    model (Base): Modelo SQLAlchemy para o tipo de controle de entrega.
    """
    existing_record = session.query(model).filter_by(doc_id=doc_id).first()

    if existing_record:
        # Atualiza o registro existente
        existing_record.client = client
        existing_record.job_title = row['Título']
        existing_record.job_link = job_link
        existing_record.used_creative_mandalecas = mandalecas
        existing_record.job_creation_date = job_creation_date
        existing_record.job_start_date = job_start_date
        existing_record.job_finish_date = job_finish_date
        existing_record.user_in_charge = user_in_charge
        existing_record.requested_by = requested_by
        existing_record.job_category = categoria
        existing_record.project_type = project_type
    else:
        # Insere um novo registro
        new_record = model(
            doc_id=doc_id,
            client=client,
            job_title=row['Título'],
            job_link=job_link,
            used_creative_mandalecas=mandalecas,
            job_creation_date=job_creation_date,
            job_start_date=job_start_date,
            job_finish_date=job_finish_date,
            user_in_charge=user_in_charge,
            requested_by=requested_by,
            job_category=categoria,
            project_type=project_type
        )
        session.add(new_record)

    session.commit()

@st.experimental_dialog("Correspondência Manual de Clientes")
def corresponder_clientes():
    """
    Abre um diálogo no Streamlit para correspondência manual de clientes não identificados automaticamente.
    """
    if st.session_state.unmatched_clients:
        session = st.session_state.session
        cliente = st.session_state.unmatched_clients[0]
        st.write(f"Correspondência manual necessária para o cliente: {cliente[1]}")

        cliente_correspondido = st.selectbox(
            "Selecione o cliente correspondente", 
            options=[c.name for c in session.query(Client).all()],
            key=f"selectbox_cliente_correspondido_{cliente[0]}"
        )
        
        novo_cliente = st.text_input("Ou adicione um novo cliente", key=f"text_input_novo_cliente_{cliente[0]}")
        
        if st.button("Confirmar", key=f"button_confirmar_cliente_{cliente[0]}"):
            confirm_client_matching(cliente, cliente_correspondido, novo_cliente, session)



def confirm_client_matching(cliente, cliente_correspondido, novo_cliente, session):
    """
    Confirma a correspondência do cliente, atualizando o banco de dados e o estado da sessão.

    Parâmetros:
    cliente (tuple): O índice e nome do cliente não correspondido.
    cliente_correspondido (str): O nome do cliente selecionado.
    novo_cliente (str): O nome do novo cliente adicionado.
    session (Session): A sessão de banco de dados ativa.
    """
    try:
        if novo_cliente:
            new_db_client = Client(name=novo_cliente, aliases=[cliente[1]])
            session.add(new_db_client)
            st.session_state.client_name_map[cliente[0]] = new_db_client
        else:
            db_client = session.query(Client).filter_by(name=cliente_correspondido).first()
            if db_client.aliases is None:
                db_client.aliases = []
            db_client.aliases.append(cliente[1])
            st.session_state.client_name_map[cliente[0]] = db_client

        session.commit()
        st.session_state.unmatched_clients.pop(0)

        if st.session_state.unmatched_clients:
            st.experimental_rerun()
        else:
            st.session_state.processar_categorias = True
            st.experimental_rerun()
    except Exception as e:
        logging.error(f"Erro ao confirmar correspondência do cliente: {e}", exc_info=True)
        st.error(f"Erro ao confirmar correspondência do cliente: {e}")


@st.experimental_dialog("Correspondência Manual de Categorias")
def match_categories_dialog():
    df = st.session_state.df
    unmatched_categories = st.session_state.unmatched_categories
    updated_categories = {}

    if not unmatched_categories:
        st.write("Nenhuma categoria não correspondida encontrada.")
        return

    for index in unmatched_categories:
        try:
            row = df.loc[index]
            categoria_escolhida = st.selectbox(
                f"Escolha a categoria para o job '{row['Título']}' no projeto '{row['Projeto']}'",
                options=[category.value for category in CategoryEnumCreative] + [category.value for category in CategoryEnumRedesSociais],
                key=f"categoria_{index}"
            )
            updated_categories[index] = categoria_escolhida
        except KeyError:
            logging.error(f"Índice {index} não encontrado no DataFrame.")
            st.error(f"Índice {index} não encontrado no DataFrame.")
    
    if st.button("Confirmar Todas", key="confirmar_todas_categorias"):
        confirm_category_matching(updated_categories)

def confirm_category_matching(updated_categories):
    st.session_state.unmatched_categories = []
    st.session_state.job_category_map.update(updated_categories)
    process_jobs(st.session_state.df, st.session_state.client_name_map, st.session_state.job_category_map)
    st.experimental_rerun()
    
    # Código para carregar o arquivo e processá-lo
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"], key="file_uploader_1")
if uploaded_file:
    process_xlsx_file(uploaded_file)

# Verificar se é necessário processar clientes não correspondidos
if st.session_state.get('unmatched_clients'):
    corresponder_clientes()

# Verificar se é necessário processar categorias
if st.session_state.get('processar_categorias') and st.session_state.get('unmatched_categories'):
    match_categories_dialog()

if st.button("Concluir", key="concluir_button"):
    session = Session()
    try:
        for client_data in st.session_state.clients_to_add:
            new_client = Client(
                name=client_data['name'],
                n_monthly_contracted_creative_mandalecas=client_data['creative_mandalecas'],
                n_monthly_contracted_format_adaptation_mandalecas=client_data['adaptation_mandalecas'],
                n_monthly_contracted_content_production_mandalecas=client_data['content_mandalecas'],
                aliases=client_data['aliases']
            )
            session.add(new_client)
        session.commit()
        st.success("Todos os clientes adicionados com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao adicionar novos clientes: {e}", exc_info=True)
        st.error(f"Erro ao adicionar novos clientes: {e}")
    finally:
        session.close()

   
