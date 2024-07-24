import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from common.models import DeliveryControl, Client, Users, JobCategoryEnum
from common.database import engine
from datetime import datetime
import streamlit as st
from dateutil.relativedelta import relativedelta
import logging
import sqlite3

# Configura o log
logging.basicConfig(filename='process_xlsx.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Crie uma sessão
Session = sessionmaker(bind=engine)


def get_total_feed_instagram_mandalecas(delivery_control):
    return (
        delivery_control.used_reels_instagram_mandalecas +
        delivery_control.used_carousel_mandalecas +
        delivery_control.used_card_instagram_mandalecas
    )


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

def identificar_categoria(titulo, projeto=None):
    titulo_lower = re.sub(r'[|<>]', '', str(titulo).lower()).strip()
    if 'stories' in titulo_lower and 'repost' in titulo_lower:
        return JobCategoryEnum.STORIES_REPOST_INSTAGRAM
    elif 'reels' in titulo_lower:
        return JobCategoryEnum.REELS_INSTAGRAM
    elif 'feed' in titulo_lower and 'instagram' in titulo_lower:
        return JobCategoryEnum.FEED_INSTAGRAM
    elif 'feed' in titulo_lower and 'tiktok' in titulo_lower:
        return JobCategoryEnum.FEED_TIKTOK
    elif 'feed' in titulo_lower and 'linkedin' in titulo_lower:
        return JobCategoryEnum.FEED_LINKEDIN
    elif 'stories' in titulo_lower:
        return JobCategoryEnum.STORIES_INSTAGRAM
    elif 'produção de conteúdo' in titulo_lower:
        return JobCategoryEnum.CONTENT_PRODUCTION
    elif 'criação' in titulo_lower:
        return JobCategoryEnum.CRIACAO
    elif 'adaptação' in titulo_lower:
        return JobCategoryEnum.ADAPTACAO
    elif 'tráfego pago' in titulo_lower and 'estático' in titulo_lower:
        return JobCategoryEnum.STATIC_TRAFEGO_PAGO
    elif 'tráfego pago' in titulo_lower and 'animado' in titulo_lower:
        return JobCategoryEnum.ANIMATED_TRAFEGO_PAGO
    else:
        return None
def convert_to_date(date_value):
    if isinstance(date_value, pd.Timestamp):
        return date_value.date()
    elif isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

def upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, categoria):
    logging.debug(f"upsert_delivery_control chamada para doc_id {doc_id}")
    existing_entry = session.query(DeliveryControl).filter_by(id=doc_id).first()
    mandaleca_field = None

    if categoria == JobCategoryEnum.CRIACAO.value:
        mandaleca_field = 'used_creative_mandalecas'
    elif categoria == JobCategoryEnum.ADAPTACAO.value:
        mandaleca_field = 'used_format_adaptation_mandalecas'
    elif categoria == JobCategoryEnum.CONTENT_PRODUCTION.value:
        mandaleca_field = 'used_content_production_mandalecas'
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
    elif categoria == JobCategoryEnum.STATIC_TRAFEGO_PAGO.value:
        mandaleca_field = 'used_static_trafego_pago_mandalecas'
    elif categoria == JobCategoryEnum.ANIMATED_TRAFEGO_PAGO.value:
        mandaleca_field = 'used_animated_trafego_pago_mandalecas'

    if existing_entry:
        existing_entry.client_id = client.id
        existing_entry.job_link = job_link
        existing_entry.job_title = row['Título']
        existing_entry.project = row['Projeto']  # Adicione esta linha
        if mandaleca_field:
            setattr(existing_entry, mandaleca_field, mandalecas)
            logging.info(f"Atualizando DeliveryControl com ID {doc_id}. Campo {mandaleca_field} definido como {mandalecas}.")
        existing_entry.job_creation_date = job_creation_date
        existing_entry.job_start_date = job_start_date
        existing_entry.job_finish_date = job_finish_date
        existing_entry.job_status = row['Status']
        existing_entry.category = categoria
    else:
        new_entry_args = {
            'id': doc_id,
            'client_id': client.id,
            'job_link': job_link,
            'job_title': row['Título'],
            'project': row['Projeto'],  # Adicione esta linha
            'job_creation_date': job_creation_date,
            'job_start_date': job_start_date,
            'job_finish_date': job_finish_date,
            'job_status': row['Status'],
            'category': categoria,
        }
        if mandaleca_field:
            new_entry_args[mandaleca_field] = mandalecas
            logging.info(f"Criando nova entrada em DeliveryControl com ID {doc_id}. Campo {mandaleca_field} definido como {mandalecas}.")
        
        new_entry = DeliveryControl(**new_entry_args)
        session.add(new_entry)

    session.commit()
    logging.info(f"Dados comitados para DeliveryControl com ID {doc_id}.")

def process_jobs(df, client_name_map, job_category_map, session):
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

                # Função para atualizar ou inserir controle de entrega
                upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, user_in_charge, requested_by, categoria)

                # Consolidação das mandalecas usadas
                delivery_control = session.query(DeliveryControl).filter_by(id=doc_id).first()
                total_feed_instagram_mandalecas = get_total_feed_instagram_mandalecas(delivery_control)

                # Atualizar mandalecas contratadas para o cliente
                client.n_monthly_contracted_feed_instagram_mandalecas -= total_feed_instagram_mandalecas

                # Atualizar o cliente no banco de dados
                session.commit()
    except Exception as e:
        print(f"Erro ao processar os jobs: {e}")

def calcular_e_atualizar_mandalecas_acumuladas(client, session):
    logging.info(f"Calculando mandalecas acumuladas para o cliente: {client.name}")

    job_mais_antigo = session.query(DeliveryControl).filter_by(client_id=client.id).order_by(DeliveryControl.job_creation_date).first()

    if not job_mais_antigo:
        logging.info("Nenhum trabalho encontrado para o cliente.")
        return

    data_mais_antiga = job_mais_antigo.job_creation_date
    data_atual = datetime.now()
    numero_meses = relativedelta(data_atual, data_mais_antiga).years * 12 + relativedelta(data_atual, data_mais_antiga).months + 1

    mandalecas_contratadas_criacao = numero_meses * (client.n_monthly_contracted_creative_mandalecas or 0)
    mandalecas_contratadas_adaptacao = numero_meses * (client.n_monthly_contracted_format_adaptation_mandalecas or 0)
    mandalecas_contratadas_conteudo = numero_meses * (client.n_monthly_contracted_content_production_mandalecas or 0)
    mandalecas_contratadas_stories_instagram = numero_meses * (client.n_monthly_contracted_stories_instagram_mandalecas or 0)
    mandalecas_contratadas_feed_linkedin = numero_meses * (client.n_monthly_contracted_feed_linkedin_mandalecas or 0)
    mandalecas_contratadas_feed_tiktok = numero_meses * (client.n_monthly_contracted_feed_tiktok_mandalecas or 0)
    mandalecas_contratadas_stories_repost_instagram = numero_meses * (client.n_monthly_contracted_stories_repost_instagram_mandalecas or 0)
    mandalecas_contratadas_feed_instagram = numero_meses * (client.n_monthly_contracted_feed_instagram_mandalecas or 0)
    mandalecas_contratadas_static_trafego_pago = numero_meses * (client.n_monthly_contracted_trafego_pago_static or 0)
    mandalecas_contratadas_animated_trafego_pago = numero_meses * (client.n_monthly_contracted_trafego_pago_animated or 0)

    entregas = session.query(DeliveryControl).filter_by(client_id=client.id).all()
    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.CRIACAO.value)
    mandalecas_usadas_adaptacao = sum((entrega.used_format_adaptation_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.ADAPTACAO.value)
    mandalecas_usadas_conteudo = sum((entrega.used_content_production_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.CONTENT_PRODUCTION.value)
    mandalecas_usadas_stories_instagram = sum((entrega.used_stories_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STORIES_INSTAGRAM.value)
    mandalecas_usadas_feed_linkedin = sum((entrega.used_feed_linkedin_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_LINKEDIN.value)
    mandalecas_usadas_feed_tiktok = sum((entrega.used_feed_tiktok_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_TIKTOK.value)
    mandalecas_usadas_stories_repost_instagram = sum((entrega.used_stories_repost_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STORIES_REPOST_INSTAGRAM.value)
    mandalecas_usadas_feed_instagram = sum((entrega.used_feed_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_INSTAGRAM.value)
    mandalecas_usadas_static_trafego_pago = sum((entrega.used_static_trafego_pago_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STATIC_TRAFEGO_PAGO.value)
    mandalecas_usadas_animated_trafego_pago = sum((entrega.used_animated_trafego_pago_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.ANIMATED_TRAFEGO_PAGO.value)

    client.accumulated_creative_mandalecas = mandalecas_contratadas_criacao - mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_contratadas_adaptacao - mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_contratadas_conteudo - mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_contratadas_stories_instagram - mandalecas_usadas_stories_instagram
    client.accumulated_feed_linkedin_mandalecas = mandalecas_contratadas_feed_linkedin - mandalecas_usadas_feed_linkedin
    client.accumulated_feed_tiktok_mandalecas = mandalecas_contratadas_feed_tiktok - mandalecas_usadas_feed_tiktok
    client.accumulated_stories_repost_mandalecas = mandalecas_contratadas_stories_repost_instagram - mandalecas_usadas_stories_repost_instagram
    client.accumulated_feed_instagram_mandalecas = mandalecas_contratadas_feed_instagram - mandalecas_usadas_feed_instagram
    client.accumulated_static_trafego_pago = mandalecas_contratadas_static_trafego_pago - mandalecas_usadas_static_trafego_pago
    client.accumulated_animated_trafego_pago = mandalecas_contratadas_animated_trafego_pago - mandalecas_usadas_animated_trafego_pago

    logging.info(f"Valores atualizados para o cliente {client.name}: "
                 f"Criação: {client.accumulated_creative_mandalecas}, "
                 f"Adaptação: {client.accumulated_format_adaptation_mandalecas}, "
                 f"Conteúdo: {client.accumulated_content_mandalecas}, "
                 f"Stories: {client.accumulated_stories_mandalecas}, "
                 f"Feed LinkedIn: {client.accumulated_feed_linkedin_mandalecas}, "
                 f"Feed TikTok: {client.accumulated_feed_tiktok_mandalecas}, "
                 f"Stories Repost: {client.accumulated_stories_repost_mandalecas}, "
                 f"Feed Instagram: {client.accumulated_feed_instagram_mandalecas}, "
                 f"Static Tráfego Pago: {client.accumulated_static_trafego_pago}, "
                 f"Animated Tráfego Pago: {client.accumulated_animated_trafego_pago}")

    session.commit()

def read_excel_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    logging.info(f"Arquivo XLSX lido com sucesso. Colunas: {df.columns.tolist()}")
    return df

def match_clients_in_dataframe(df, session):
    unmatched_clients = []
    client_name_map = {}
    existing_clients = {client.name: client for client in session.query(Client).all()}

    for index, row in df.iterrows():
        client_name = str(row['Cliente']).strip()
        client = existing_clients.get(client_name) or session.query(Client).filter(Client.aliases.contains([client_name])).first()
        if not client:
            unmatched_clients.append((index, client_name))
        else:
            client_name_map[index] = client

    if unmatched_clients:
        logging.warning(f"Clientes não correspondidos: {unmatched_clients}")
    else:
        logging.info("Todos os clientes foram correspondidos com sucesso.")
    return unmatched_clients, client_name_map

def match_categories_in_dataframe(df, client_name_map):
    unmatched_categories = []
    job_category_map = {}

    for index, row in df.iterrows():
        categoria = identificar_categoria(row['Título'], row['Projeto'])
        if not categoria:
            unmatched_categories.append((index, row['Título']))
        else:
            job_category_map[index] = categoria

    if unmatched_categories:
        logging.warning(f"Categorias não correspondidas: {unmatched_categories}")
    else:
        logging.info("Todas as categorias foram correspondidas com sucesso.")
    return unmatched_categories, job_category_map

def handle_unmatched_entities(unmatched_clients, unmatched_categories, df, client_name_map, job_category_map, session):
    if not unmatched_clients and not unmatched_categories:
        logging.info("Iniciando processamento dos trabalhos.")
        process_jobs(df, client_name_map, job_category_map, session)
    else:
        logging.error("Existem clientes ou categorias não correspondidos. Não é possível processar os trabalhos.")

def process_xlsx_file(file):
    # Código para abrir e ler o arquivo XLSX
    df = pd.read_excel(file)

    for index, row in df.iterrows():
        job_category = identificar_categoria(row['Título'])  # Supondo que identificar_categoria retorna JobCategoryEnum
        if job_category is None:
            # Lógica para lidar com títulos não correspondidos
            continue

        delivery_category = map_category_to_delivery_category(job_category)

        new_delivery_control = DeliveryControl(
            # ... outros campos extraídos da linha do arquivo
            job_category=job_category,
            delivery_category=delivery_category,
            # ...
        )

        session.add(new_delivery_control)
    
    session.commit()