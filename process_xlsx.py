import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from common.models import DeliveryControl, Client, Users, JobCategoryEnum
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

def initialize_session_state():
    if 'clientes_nao_correspondidos' not in st.session_state:
        st.session_state.clientes_nao_correspondidos = []
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

def extract_mandalecas(title):
    match = re.search(r'mdl\s?(\d+[.,]?\d*)', title, re.IGNORECASE)
    if match:
        mandalecas = match.group(1).replace(',', '.')
        return float(mandalecas)
    return None

def identificar_categoria(titulo, projeto):
    titulo_lower = re.sub(r'[|<>]', '', str(titulo).lower()).strip()  # Remover caracteres especiais e espaços extras
    # Mapear palavras-chave para categorias do Enum
    if 'stories' in titulo_lower and 'repost' in titulo_lower:
        return JobCategoryEnum.STORIES_REPOST_INSTAGRAM.value
    elif 'reels' in titulo_lower:
        return JobCategoryEnum.REELS_INSTAGRAM.value
    elif 'feed' in titulo_lower and 'instagram' in titulo_lower:
        return JobCategoryEnum.FEED_INSTAGRAM.value
    elif 'feed' in titulo_lower and 'tiktok' in titulo_lower:
        return JobCategoryEnum.FEED_TIKTOK.value
    elif 'feed' in titulo_lower and 'linkedin' in titulo_lower:
        return JobCategoryEnum.FEED_LINKEDIN.value
    elif 'stories' in titulo_lower:
        return JobCategoryEnum.STORIES_INSTAGRAM.value
    elif 'produção de conteúdo' in titulo_lower:
        return JobCategoryEnum.CONTENT_PRODUCTION.value
    elif 'criação' in titulo_lower:
        return JobCategoryEnum.CRIACAO.value
    elif 'adaptação' in titulo_lower:
        return JobCategoryEnum.ADAPTACAO.value
    else:
        return None

def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

def calcular_e_atualizar_mandalecas_acumuladas(client, session):
    logging.info(f"Calculando mandalecas acumuladas para o cliente: {client.name}")

    # Consultar o trabalho mais antigo para DeliveryControl
    job_mais_antigo = session.query(DeliveryControl).filter_by(client_id=client.id).order_by(DeliveryControl.job_creation_date).first()

    if not job_mais_antigo:
        logging.info("Nenhum trabalho encontrado para o cliente.")
        return

    data_mais_antiga = job_mais_antigo.job_creation_date
    data_atual = datetime.now()
    numero_meses = relativedelta(data_atual, data_mais_antiga).years * 12 + relativedelta(data_atual, data_mais_antiga).months + 1

    # Calcular mandalecas contratadas para DeliveryControl
    mandalecas_contratadas_criacao = numero_meses * (client.n_monthly_contracted_creative_mandalecas or 0)
    mandalecas_contratadas_adaptacao = numero_meses * (client.n_monthly_contracted_format_adaptation_mandalecas or 0)
    mandalecas_contratadas_conteudo = numero_meses * (client.n_monthly_contracted_content_production_mandalecas or 0)
    mandalecas_contratadas_stories_instagram = numero_meses * (client.n_monthly_contracted_stories_instagram_mandalecas or 0)
    mandalecas_contratadas_feed_linkedin = numero_meses * (client.n_monthly_contracted_feed_linkedin_mandalecas or 0)
    mandalecas_contratadas_feed_tiktok = numero_meses * (client.n_monthly_contracted_feed_tiktok_mandalecas or 0)
    mandalecas_contratadas_stories_repost_instagram = numero_meses * (client.n_monthly_contracted_stories_repost_instagram_mandalecas or 0)
    mandalecas_contratadas_reels_instagram = numero_meses * (client.n_monthly_contracted_reels_instagram_mandalecas or 0)
    mandalecas_contratadas_feed_instagram = numero_meses * (client.n_monthly_contracted_feed_instagram_mandalecas or 0)

    # Consultar entregas para DeliveryControl
    entregas = session.query(DeliveryControl).filter_by(client_id=client.id).all()
    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.CRIACAO.value)
    mandalecas_usadas_adaptacao = sum((entrega.used_format_adaptation_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.ADAPTACAO.value)
    mandalecas_usadas_conteudo = sum((entrega.used_content_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.CONTENT_PRODUCTION.value)
    mandalecas_usadas_stories_instagram = sum((entrega.used_stories_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STORIES_INSTAGRAM.value)
    mandalecas_usadas_feed_linkedin = sum((entrega.used_feed_linkedin_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_LINKEDIN.value)
    mandalecas_usadas_feed_tiktok = sum((entrega.used_feed_tiktok_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_TIKTOK.value)
    mandalecas_usadas_stories_repost_instagram = sum((entrega.used_stories_repost_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STORIES_REPOST_INSTAGRAM.value)
    mandalecas_usadas_reels_instagram = sum((entrega.used_reels_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.REELS_INSTAGRAM.value)
    mandalecas_usadas_feed_instagram = sum((entrega.used_feed_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_INSTAGRAM.value)

    # Atualizar acumulados para DeliveryControl
    client.accumulated_creative_mandalecas = mandalecas_contratadas_criacao - mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_contratadas_adaptacao - mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_contratadas_conteudo - mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_contratadas_stories_instagram - mandalecas_usadas_stories_instagram
    client.accumulated_feed_linkedin_mandalecas = mandalecas_contratadas_feed_linkedin - mandalecas_usadas_feed_linkedin
    client.accumulated_feed_tiktok_mandalecas = mandalecas_contratadas_feed_tiktok - mandalecas_usadas_feed_tiktok
    client.accumulated_stories_repost_mandalecas = mandalecas_contratadas_stories_repost_instagram - mandalecas_usadas_stories_repost_instagram
    client.accumulated_reels_mandalecas = mandalecas_contratadas_reels_instagram - mandalecas_usadas_reels_instagram
    client.accumulated_feed_instagram_mandalecas = mandalecas_contratadas_feed_instagram - mandalecas_usadas_feed_instagram

    # Log dos valores atualizados
    logging.info(f"Valores atualizados para o cliente {client.name}: "
                 f"Criação: {client.accumulated_creative_mandalecas}, "
                 f"Adaptação: {client.accumulated_format_adaptation_mandalecas}, "
                 f"Conteúdo: {client.accumulated_content_mandalecas}, "
                 f"Stories: {client.accumulated_stories_mandalecas}, "
                 f"Feed LinkedIn: {client.accumulated_feed_linkedin_mandalecas}, "
                 f"Feed TikTok: {client.accumulated_feed_tiktok_mandalecas}, "
                 f"Stories Repost: {client.accumulated_stories_repost_mandalecas}, "
                 f"Reels: {client.accumulated_reels_mandalecas}, "
                 f"Feed Instagram: {client.accumulated_feed_instagram_mandalecas}")

    # Commit para salvar as alterações
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

def handle_unmatched_entities(unmatched_clients, unmatched_categories, df, client_name_map, job_category_map, session):
    if not unmatched_clients and not unmatched_categories:
        process_jobs(df, client_name_map, job_category_map, session)


def process_xlsx_file(uploaded_file):
    initialize_session_state()
    session = Session()  # Crie uma sessão
    try:
        df = read_excel_file(uploaded_file)
        
        # Remover linhas onde a coluna 'Cliente' tenha valores NaN ou in branco
        df = df.dropna(subset=['Cliente']).reset_index(drop=True)
        df = df[df['Cliente'].str.strip().astype(bool)]
        
        st.session_state.df = df

        unmatched_clients, client_name_map = match_clients_in_dataframe(df, session)
        unmatched_categories, job_category_map = match_categories_in_dataframe(df, client_name_map)

        st.session_state.unmatched_clients = unmatched_clients
        st.session_state.client_name_map = client_name_map
        st.session_state.unmatched_categories = unmatched_categories
        st.session_state.job_category_map = job_category_map
        st.session_state.session = session  # Armazenar a sessão no estado

        # Prints de verificação
        if unmatched_clients:
            st.write("Clientes não encontrados no banco de dados:")
            for idx, client in unmatched_clients:
                st.write(f"Índice: {idx}, Cliente: {client}")
        else:
            st.write("Todos os clientes foram encontrados e correspondidos.")

        if unmatched_categories:
            st.write("Categorias não encontradas no banco de dados:")
            for idx, category in unmatched_categories:
                st.write(f"Índice: {idx}, Categoria: {category}")
        else:
            st.write("Todas as categorias foram encontradas e correspondidas.")

        handle_unmatched_entities(unmatched_clients, unmatched_categories, df, client_name_map, job_category_map, session)

    except Exception as e:
        logging.error(f"Erro ao processar dados: {e}", exc_info=True)
        st.error(f"Erro ao processar dados: {e}")
    finally:
        session.close()  # Certifique-se de fechar a sessão

def handle_unmatched_entities(unmatched_clients, unmatched_categories, df, client_name_map, job_category_map, session):
    if not unmatched_clients and not unmatched_categories:
        process_jobs(df, client_name_map, job_category_map, session)


def process_jobs(df, client_name_map, job_category_map, session):
    try:
        for index, row in df.iterrows():
            if index in client_name_map:
                client = client_name_map[index]
                user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()

                doc_num = str(row['Nº Doc']).split('.')[0]
                job_link = f"https://app4.operand.com.br/jobs/{doc_num}"

                mandalecas = extract_mandalecas(row['Título'])
                categoria = job_category_map.get(index)

                doc_id = int(doc_num)

                job_creation_date = convert_to_date(row['Data de criação'])
                job_start_date = convert_to_date(row['Data Início'])
                job_finish_date = convert_to_date(row['Data de Conclusão'])

                upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, user_in_charge, categoria)

        for client in set(client_name_map.values()):
            calcular_e_atualizar_mandalecas_acumuladas(client, session)
        
        st.write("Dados processados e inseridos com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao processar trabalhos: {e}", exc_info=True)
        st.error(f"Erro ao processar trabalhos: {e}")

def upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, user_in_charge, categoria):
    """
    Insere ou atualiza uma entrada de controle de entrega no banco de dados.

    Parâmetros:
    session (Session): A sessão de banco de dados ativa.
    doc_id (int): O ID do documento.
    client (Client): O cliente associado ao trabalho.
    row (pd.Series): A linha do DataFrame contendo os dados do trabalho.
    job_link (str): O link do trabalho.
    mandalecas (float): O número de mandalecas usadas.
    job_creation_date (datetime.date): A data de criação do trabalho.
    job_start_date (datetime.date): A data de início do trabalho.
    job_finish_date (datetime.date): A data de conclusão do trabalho.
    user_in_charge (Users): O usuário responsável pelo trabalho.
    categoria (str): A categoria do trabalho.
    """
    existing_entry = session.query(DeliveryControl).filter_by(id=doc_id).first()

    mandaleca_field = None
    if categoria == JobCategoryEnum.CRIACAO.value:
        mandaleca_field = 'used_creative_mandalecas'
    elif categoria == JobCategoryEnum.ADAPTACAO.value:
        mandaleca_field = 'used_format_adaptation_mandalecas'
    elif categoria == JobCategoryEnum.CONTENT_PRODUCTION.value:
        mandaleca_field = 'used_content_mandalecas'
    elif categoria == JobCategoryEnum.STORIES_INSTAGRAM.value:
        mandaleca_field = 'used_stories_instagram_mandalecas'
    elif categoria == JobCategoryEnum.FEED_LINKEDIN.value:
        mandaleca_field = 'used_feed_linkedin_mandalecas'
    elif categoria == JobCategoryEnum.FEED_TIKTOK.value:
        mandaleca_field = 'used_feed_tiktok_mandalecas'
    elif categoria == JobCategoryEnum.STORIES_REPOST_INSTAGRAM.value:
        mandaleca_field = 'used_stories_repost_instagram_mandalecas'
    elif categoria == JobCategoryEnum.REELS_INSTAGRAM.value:
        mandaleca_field = 'used_reels_instagram_mandalecas'
    elif categoria == JobCategoryEnum.FEED_INSTAGRAM.value:
        mandaleca_field = 'used_feed_instagram_mandalecas'

    if existing_entry:
        existing_entry.client_id = client.id
        existing_entry.job_link = job_link
        existing_entry.job_title = row['Título']
        if mandaleca_field:
            setattr(existing_entry, mandaleca_field, mandalecas)
            logging.info(f"Atualizando DeliveryControl com ID {doc_id}. Campo {mandaleca_field} definido como {mandalecas}.")
        existing_entry.job_creation_date = job_creation_date
        existing_entry.job_start_date = job_start_date
        existing_entry.job_finish_date = job_finish_date
        existing_entry.job_status = row['Status']
        existing_entry.user_in_charge_id = user_in_charge.id if user_in_charge else None
        existing_entry.requested_by_id = None
        existing_entry.category = categoria
        existing_entry.project = row['Projeto']
    else:
        new_entry_args = {
            'id': doc_id,
            'client_id': client.id,
            'job_link': job_link,
            'job_title': row['Título'],
            'job_creation_date': job_creation_date,
            'job_start_date': job_start_date,
            'job_finish_date': job_finish_date,
            'job_status': row['Status'],
            'user_in_charge_id': user_in_charge.id if user_in_charge else None,
            'requested_by_id': None,
            'category': categoria,
            'project': row['Projeto']
        }
        if mandaleca_field:
            new_entry_args[mandaleca_field] = mandalecas
            logging.info(f"Criando nova entrada in DeliveryControl com ID {doc_id}. Campo {mandaleca_field} definido como {mandalecas}.")
        
        new_entry = DeliveryControl(**new_entry_args)
        session.add(new_entry)

    session.commit()
    logging.info(f"Dados comitados para DeliveryControl com ID {doc_id}.")



# Código para carregar o arquivo e processá-lo
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"], key="file_uploader_1")
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state.df = df
    process_xlsx_file(uploaded_file)
