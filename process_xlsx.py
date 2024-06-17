import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, DeliveryControlRedesSociais, Client, Users, CategoryEnumCreative, CategoryEnumRedesSociais
from common.database import engine
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import streamlit as st
import uuid
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
import logging

# Configura o log
logging.basicConfig(filename='process_xlsx.log', level=logging.ERROR)

# Crie uma sessão
Session = sessionmaker(bind=engine)

# Função para extrair o número de mandalecas
def extract_mandalecas(title):
    match = re.search(r'mdl\s?(\d+[.,]?\d*)', title, re.IGNORECASE)
    if match:
        mandalecas = match.group(1).replace(',', '.')
        return float(mandalecas)
    return None

# Função para identificar a categoria do trabalho
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

# Função para converter valores para data
def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

# Função para calcular e atualizar mandalecas acumuladas
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
    mandalecas_usadas_reels = sum ((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Reels")
    mandalecas_usadas_stories = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Stories")
    mandalecas_usadas_cards = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Cards")
    
    client.accumulated_creative_mandalecas = mandalecas_contratadas_criacao - mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_contratadas_adaptacao - mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_contratadas_conteudo - mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_contratadas_stories - mandalecas_usadas_stories
    client.accumulated_reels_mandalecas = mandalecas_contratadas_reels - mandalecas_usadas_reels
    client.accumulated_cards_mandalecas = mandalecas_contratadas_cards - mandalecas_usadas_cards
    
    session.commit()

def process_xlsx(file):
    try:
        # Verifica se o arquivo é um Excel
        if not file.name.endswith(('.xlsx', '.xls')):
            raise ValueError("O arquivo enviado não é um arquivo Excel")

        # Tenta ler o arquivo Excel
        df = pd.read_excel(file)

        # Verifica se as colunas esperadas estão presentes
        expected_columns = ["Cliente", "Projeto", "Título"]
        for column in expected_columns:
            if column not in df.columns:
                raise ValueError(f"A coluna esperada '{column}' não está presente no arquivo Excel")

        # Realiza outras validações se necessário
        # ...

        return df

    except ValueError as ve:
        print(f"Erro de validação: {ve}")
        st.error(f"Erro de validação: {ve}")
    except Exception as e:
        print(f"Erro ao processar o arquivo Excel: {e}")
        st.error(f"Erro ao processar o arquivo Excel: {e}")

def read_and_transform_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    
    # Conversão de campos de data para o formato datetime
    df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Tratamento do campo "Nº Doc"
    df['Nº Doc'] = df['Nº Doc'].apply(lambda x: int(str(x).split('.')[0]) if pd.notna(x) else None)
    
    return df

def initialize_session_state():
    # Inicializa as listas e dicionários no session_state
    st.session_state.unmatched_clients = []  # Lista de clientes não correspondidos
    st.session_state.client_name_map = {}  # Mapeamento de nomes de clientes
    st.session_state.clients_to_add = []  # Lista de clientes a serem adicionados
    st.session_state.actions_taken = []  # Lista de ações realizadas
    st.session_state.unmatched_categories = []  # Lista de categorias de trabalho não correspondidas
    st.session_state.job_category_map = {}  # Mapeamento de categorias de trabalho
    st.session_state.df = None  # DataFrame do arquivo XLSX lido
    st.session_state.session = None  # Sessão do banco de dados

def get_existing_clients(session: Session):
    # Obtem todos os clientes do banco de dados e cria um dicionário com o nome do cliente como chave
    existing_clients = {client.name: client for client in session.query(Client).all()}
    return existing_clients


def match_clients(df, existing_clients, session):
    unmatched_clients = []
    client_name_map = {}

    for index, row in df.iterrows():
        client_name = str(row['Cliente'])
        client = existing_clients.get(client_name)

        if not client:
            client = session.query(Client).filter(Client.aliases.contains([client_name])).first()

        if not client:
            unmatched_clients.append((index, client_name))
        else:
            client_name_map[index] = client

    if unmatched_clients:
        st.session_state.unmatched_clients = unmatched_clients
        st.session_state.client_name_map = client_name_map

    return unmatched_clients, client_name_map

@st.experimental_dialog("Correspondência de Clientes", width="large")
def match_client_dialog():
    if not st.session_state.get("unmatched_clients"):
        return

    index, client_name = st.session_state.unmatched_clients[0]
    session = st.session_state.session
    existing_clients = [client.name for client in session.query(Client).all()]
    new_clients = [client['name'] for client in st.session_state.get('clients_to_add', [])]
    all_clients = existing_clients + new_clients

    action = st.radio(
        "Ação:",
        ("Corresponder a um cliente existente", "Adicionar como novo cliente"),
        key=f"action_{index}"
    )

    if action == "Corresponder a um cliente existente":
        selected_client_name = st.selectbox(
            "Selecione o cliente correspondente:",
            all_clients,
            key=f"client_{index}"
        )
        if st.button("Confirmar Correspondência", key=f"confirm_match_{index}"):
            selected_client = session.query(Client).filter_by(name=selected_client_name).first()
            if not selected_client:
                selected_client = next((client for client in st.session_state.clients_to_add if client['name'] == selected_client_name), None)
            if selected_client:
                if not isinstance(selected_client, dict):
                    if not selected_client.aliases:
                        selected_client.aliases = []
                    selected_client.aliases.append(client_name)
                else:
                    if 'aliases' not in selected_client:
                        selected_client['aliases'] = []
                    selected_client['aliases'].append(client_name)
                st.session_state.client_name_map[index] = selected_client
                st.session_state.unmatched_clients.pop(0)
                st.session_state.actions_taken.append("correspondido")
                if not st.session_state.unmatched_clients:
                    st.rerun()

    elif action == "Adicionar como novo cliente":
        new_client_name = st.text_input("Nome do cliente", value=client_name)
        creative_mandalecas = st.number_input("Mandalecas mensais contratadas (Criação)", min_value=0)
        adaptation_mandalecas = st.number_input("Mandalecas mensais contratadas (Adaptação)", min_value=0)
        content_mandalecas = st.number_input("Mandalecas mensais contratadas (Conteúdo)", min_value=0)
        if st.button("Confirmar Adição", key=f"confirm_add_{index}"):
            new_client = {
                'name': new_client_name,
                'creative_mandalecas': creative_mandalecas,
                'adaptation_mandalecas': adaptation_mandalecas,
                'content_mandalecas': content_mandalecas,
                'aliases': [client_name]
            }
            st.session_state.clients_to_add.append(new_client)
            st.session_state.client_name_map[index] = new_client
            st.session_state.unmatched_clients.pop(0)
            st.session_state.actions_taken.append("adicionado")
            if not st.session_state.unmatched_clients:
                st.rerun()

    if st.button("Ignorar", key=f"ignore_button_{index}"):
        st.session_state.unmatched_clients.pop(0)
        st.session_state.actions_taken.append("ignorado")
        if not st.session_state.unmatched_clients:
            st.rerun()

    if st.button("Voltar", key=f"back_button_{index}"):
        if st.session_state.actions_taken:
            last_action = st.session_state.actions_taken.pop()
            if last_action in ["correspondido", "ignorado"]:
                st.session_state.unmatched_clients.insert(0, (index, client_name))
            elif last_action == "adicionado":
                st.session_state.unmatched_clients.insert(0, (index, client_name))
                st.session_state.clients_to_add.pop()
            st.rerun()


def match_categories(df):
    unmatched_categories = []
    job_category_map = {}

    for index, row in df.iterrows():
        categoria = identificar_categoria(row['Título'], row['Projeto'])
        if not categoria:
            unmatched_categories.append((index, row['Título']))
        else:
            job_category_map[index] = categoria

    return unmatched_categories, job_category_map

@st.experimental_dialog("Correspondência de Clientes", width="large")
def match_client_dialog():
    if not st.session_state.get("unmatched_clients"):
        return

    index, client_name = st.session_state.unmatched_clients[0]
    session = st.session_state.session
    existing_clients = [client.name for client in session.query(Client).all()]
    new_clients = [client['name'] for client in st.session_state.get('clients_to_add', [])]
    all_clients = existing_clients + new_clients

    action = st.radio(
        "Ação:",
        ("Corresponder a um cliente existente", "Adicionar como novo cliente"),
        key=f"action_{index}"
    )

    if action == "Corresponder a um cliente existente":
        selected_client_name = st.selectbox(
            "Selecione o cliente correspondente:",
            all_clients,
            key=f"client_{index}"
        )
        if st.button("Confirmar Correspondência", key=f"confirm_match_{index}"):
            selected_client = session.query(Client).filter_by(name=selected_client_name).first()
            if not selected_client:
                selected_client = next((client for client in st.session_state.clients_to_add if client['name'] == selected_client_name), None)
            if selected_client:
                if not isinstance(selected_client, dict):
                    if not selected_client.aliases:
                        selected_client.aliases = []
                    selected_client.aliases.append(client_name)
                else:
                    if 'aliases' not in selected_client:
                        selected_client['aliases'] = []
                    selected_client['aliases'].append(client_name)
                st.session_state.client_name_map[index] = selected_client
                st.session_state.unmatched_clients.pop(0)
                st.session_state.actions_taken.append("correspondido")
                print("Cliente Correspondido:", client_name)
                print("Clientes não correspondidos restantes:", st.session_state.unmatched_clients)
                if not st.session_state.unmatched_clients:
                    print("Todos os clientes foram correspondidos.")
                    st.rerun()

    elif action == "Adicionar como novo cliente":
        new_client_name = st.text_input("Nome do cliente", value=client_name)
        creative_mandalecas = st.number_input("Mandalecas mensais contratadas (Criação)", min_value=0)
        adaptation_mandalecas = st.number_input("Mandalecas mensais contratadas (Adaptação)", min_value=0)
        content_mandalecas = st.number_input("Mandalecas mensais contratadas (Conteúdo)", min_value=0)
        if st.button("Confirmar Adição", key=f"confirm_add_{index}"):
            new_client = {
                'name': new_client_name,
                'creative_mandalecas': creative_mandalecas,
                'adaptation_mandalecas': adaptation_mandalecas,
                'content_mandalecas': content_mandalecas,
                'aliases': [client_name]
            }
            st.session_state.clients_to_add.append(new_client)
            st.session_state.client_name_map[index] = new_client
            st.session_state.unmatched_clients.pop(0)
            st.session_state.actions_taken.append("adicionado")
            print("Novo Cliente Adicionado:", new_client_name)
            print("Clientes não correspondidos restantes:", st.session_state.unmatched_clients)
            if not st.session_state.unmatched_clients:
                print("Todos os clientes foram adicionados.")
                st.rerun()

    if st.button("Ignorar", key=f"ignore_button_{index}"):
        st.session_state.unmatched_clients.pop(0)
        st.session_state.actions_taken.append("ignorado")
        print("Cliente Ignorado:", client_name)
        print("Clientes não correspondidos restantes:", st.session_state.unmatched_clients)
        if not st.session_state.unmatched_clients:
            print("Todos os clientes foram ignorados.")
            st.rerun()

    if st.button("Voltar", key=f"back_button_{index}"):
        if st.session_state.actions_taken:
            last_action = st.session_state.actions_taken.pop()
            if last_action in ["correspondido", "ignorado"]:
                st.session_state.unmatched_clients.insert(0, (index, client_name))
            elif last_action == "adicionado":
                st.session_state.unmatched_clients.insert(0, (index, client_name))
                st.session_state.clients_to_add.pop()
            print("Ação desfeita:", last_action)
            st.rerun()

def analyze_project_field(df):
    try:
        for index, row in df.iterrows():
            project = row['Projeto']
            if 'Redes Sociais' in project:
                update_delivery_control_redes_sociais(row)
            else:
                update_delivery_control_creative(row)

    except Exception as e:
        st.error(f"Erro ao analisar o campo 'Projeto': {e}")

def update_delivery_control_redes_sociais(row):
    try:
        # Lógica para atualizar DeliveryControlRedesSociais
        titulo = row['Título']
        # Adicione sua lógica específica para atualizar o modelo DeliveryControlRedesSociais
        # Verifique a correspondência de categoria e faça as atualizações necessárias
    except Exception as e:
        st.error(f"Erro ao atualizar DeliveryControlRedesSociais: {e}")

def update_delivery_control_creative(row):
    try:
        # Lógica para atualizar DeliveryControlCreative
        titulo = row['Título']
        # Adicione sua lógica específica para atualizar o modelo DeliveryControlCreative
        # Verifique a correspondência de categoria e faça as atualizações necessárias
    except Exception as e:
        st.error(f"Erro ao atualizar DeliveryControlCreative: {e}")

def update_session_state(df, session, unmatched_clients, client_name_map, unmatched_categories, job_category_map):
    st.session_state.df = df
    st.session_state.session = session
    st.session_state.unmatched_clients = unmatched_clients
    st.session_state.client_name_map = client_name_map
    st.session_state.clients_to_add = []
    st.session_state.actions_taken = []
    st.session_state.unmatched_categories = unmatched_categories
    st.session_state.job_category_map = job_category_map

def process_xlsx_file(uploaded_file):
    session = Session()
    try:
        # Ler e transformar o arquivo XLSX
        df = read_and_transform_excel(uploaded_file)
        
        # Inicializar o session_state
        initialize_session_state()
        
        # Obter clientes existentes do banco de dados
        existing_clients = get_existing_clients(session)
        
        # Fazer correspondência automática de clientes
        unmatched_clients, client_name_map = match_clients(df, existing_clients, session)
        
        # Atualizar o session_state com os dados processados
        update_session_state(df, session, unmatched_clients, client_name_map, [], {})
        
        # Se houver clientes não correspondidos, chamar o diálogo de correspondência manual
        if unmatched_clients:
            print("Clientes não correspondidos encontrados, iniciando correspondência manual.")
            match_client_dialog()
        # Se não houver clientes não correspondidos, continuar com o processamento
        else:
            unmatched_categories, job_category_map = match_categories(df)
            update_session_state(df, session, unmatched_clients, client_name_map, unmatched_categories, job_category_map)
            if unmatched_categories:
                print("Categorias não correspondidas encontradas, iniciando correspondência manual.")
                match_categories_dialog()
            else:
                print("Todos os dados foram correspondidos automaticamente.")
                process_jobs(df, client_name_map, job_category_map, session)
    
    except Exception as e:
        # Logar o erro e mostrar uma mensagem de erro no Streamlit
        logging.error(f"Erro ao processar dados: {e}")
        st.error(f"Erro ao processar dados: {e}")
    finally:
        session.close()

def process_jobs(df, client_name_map, job_category_map, session: Session):
    try:
        for index, row in df.iterrows():
            # Determinar qual modelo atualizar com base no campo "Projeto"
            project = row['Projeto'].lower()
            if 'redes sociais' in project:
                model = DeliveryControlRedesSociais
                category_enum = CategoryEnumRedesSociais
            else:
                model = DeliveryControlCreative
                category_enum = CategoryEnumCreative

            # Obter os valores correspondentes dos dicionários de mapeamento
            client = client_name_map.get(index)
            category = job_category_map.get(index)

            # Verificar se todos os dados necessários estão disponíveis
            if not client or not category:
                st.warning(f"Dados insuficientes para o job no índice {index}.")
                continue

            # Validar dados antes de salvar
            if not validate_job_data(row, client, category):
                st.warning(f"Dados inválidos para o job no índice {index}.")
                continue

            # Criar ou atualizar o registro no banco de dados
            job_id = row['Nº Doc']
            job = session.query(model).filter_by(id=job_id).first()
            if not job:
                job = model(id=job_id)

            # Atualizar os campos do job
            job.updated_at = datetime.utcnow()
            job.client_id = client.id if not isinstance(client, dict) else None
            job.project = row['Projeto']
            job.category = category
            job.job_title = row['Título']
            job.job_creation_date = row['Data de criação']
            job.job_start_date = row['Data Início']
            job.job_finish_date = row['Data de Conclusão']
            job.job_status = row['Status']
            job.user_in_charge_id = get_user_id_by_name(row['Responsável'], session)  # Implementar função para obter o ID do usuário pelo nome
            job.job_deadline_met = True if row['Concluído no prazo'].lower() == 'sim' else False

            # Adicionar o job à sessão
            session.add(job)
        
        # Commit após processar todos os jobs
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Erro ao processar jobs: {e}")
        st.error(f"Erro ao processar jobs: {e}")

def validate_job_data(row, client, category):
    # Adicione aqui as validações necessárias para os dados do job
    if not client or not category:
        return False
    if not row['Nº Doc'] or not row['Projeto'] or not row['Título']:
        return False
    # Adicione outras validações conforme necessário
    return True

def get_user_id_by_name(name, session: Session):
    user = session.query(Users).filter_by(name=name).first()
    return user.id if user else None

def validate_job_data(row, client, category):
    # Adicione aqui as validações necessárias para os dados do job
    if not client or not category:
        return False
    if not row['Nº Doc'] or not row['Projeto'] or not row['Título']:
        return False
    # Adicione outras validações conforme necessário
    return True

def get_user_id_by_name(name, session: Session):
    user = session.query(Users).filter_by(name=name).first()
    return user.id if user else None
