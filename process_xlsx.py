import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from common.models import DeliveryControl, Client, Users, JobCategoryEnum, DeliveryCategoryEnum
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

def clean_data(value):
    if pd.isna(value):
        return None
    return value


def get_total_feed_instagram_mandalecas(delivery_control):
    return (
        delivery_control.used_reels_instagram_mandalecas +
        delivery_control.used_carousel_mandalecas +
        delivery_control.used_card_instagram_mandalecas
    )

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
    elif 'feed' in titulo_lower and  'instagram' in titulo_lower:
        return JobCategoryEnum.FEED_INSTAGRAM
    elif 'feed' in titulo_lower and  'tiktok' in titulo_lower:
        return JobCategoryEnum.FEED_TIKTOK
    elif 'feed' in titulo_lower and  'linkedin' in titulo_lower:
        return JobCategoryEnum.FEED_LINKEDIN
    elif 'stories' in titulo_lower:
        return JobCategoryEnum.STORIES_INSTAGRAM
    elif 'produção de conteúdo' in titulo_lower:
        return JobCategoryEnum.CONTENT_PRODUCTION
    elif 'criação' in titulo_lower:
        return JobCategoryEnum.CRIACAO
    elif 'adaptação' in titulo_lower:
        return JobCategoryEnum.ADAPTACAO
    elif 'tráfego pago' in titulo_lower and  'estático' in titulo_lower:
        return JobCategoryEnum.STATIC_TRAFEGO_PAGO
    elif 'tráfego pago' in titulo_lower and  'animado' in titulo_lower:
        return JobCategoryEnum.ANIMATED_TRAFEGO_PAGO
    elif 'card' in titulo_lower and  'instagram' in titulo_lower:
        return JobCategoryEnum.CARD_INSTAGRAM
    elif 'carrossel' in titulo_lower and  'instagram' in titulo_lower:
        return JobCategoryEnum.CAROUSEL_INSTAGRAM
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

def map_category_to_delivery_category(category):
    if category in [JobCategoryEnum.CRIACAO, JobCategoryEnum.ADAPTACAO]:
        return DeliveryCategoryEnum.CRIACAO
    elif category in [
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM, 
        JobCategoryEnum.REELS_INSTAGRAM,
        JobCategoryEnum.FEED_INSTAGRAM,
        JobCategoryEnum.FEED_TIKTOK,
        JobCategoryEnum.FEED_LINKEDIN,
        JobCategoryEnum.STORIES_INSTAGRAM,
        JobCategoryEnum.CARD_INSTAGRAM,
        JobCategoryEnum.CAROUSEL_INSTAGRAM
    ]:
        return DeliveryCategoryEnum.REDES_SOCIAIS
    elif category in [
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO,
        JobCategoryEnum.STATIC_TRAFEGO_PAGO
    ]:
        return DeliveryCategoryEnum.TRAFEGO_PAGO
    elif category == JobCategoryEnum.CONTENT_PRODUCTION:
        return DeliveryCategoryEnum.CONTENT_PRODUCTION
    return None

def upsert_delivery_control(session, doc_id, client, row, job_link, mandalecas, job_creation_date, job_start_date, job_finish_date, categoria):
    logging.debug(f"upsert_delivery_control chamada para doc_id {doc_id}")
    existing_entry = session.query(DeliveryControl).filter_by(id=doc_id).first()

    if existing_entry:
        existing_entry.client_id = client.id
        existing_entry.job_link = clean_data(job_link)
        existing_entry.job_title = row['Título']
        existing_entry.project = clean_data(row['Projeto']) if 'Projeto' in row else None
        existing_entry.used_mandalecas = mandalecas
        logging.info(f"Atualizando DeliveryControl com ID {doc_id}. Campo used_mandalecas definido como {mandalecas}.")
        existing_entry.job_creation_date = clean_data(job_creation_date)
        existing_entry.job_start_date = clean_data(job_start_date)
        existing_entry.job_finish_date = clean_data(job_finish_date)
        existing_entry.job_status = clean_data(row['Status'])
        existing_entry.job_category = categoria.value  
        existing_entry.delivery_category = map_category_to_delivery_category(categoria).value
        existing_entry.user_in_charge_id = clean_data(row['Responsável']) if 'Responsável' in row else None
        existing_entry.project = clean_data(row['Projeto']) if 'Projeto' in row else None
        existing_entry.job_link = clean_data(job_link) if 'job_link' in row else None
        existing_entry.delivery_control_category = clean_data(row['delivery_control_category']) if 'delivery_control_category' in row else None
        existing_entry.job_deadline_date = clean_data(row['job_deadline_date']) if 'job_deadline_date' in row else None
        existing_entry.updated_by_id = clean_data(row['updated_by_id']) if 'updated_by_id' in row else None
        existing_entry.next_month_plan_sent = clean_data(row['next_month_plan_sent']) if 'next_month_plan_sent' in row else None
        existing_entry.next_month_plant_sent_date = clean_data(row['next_month_plant_sent_date']) if 'next_month_plant_sent_date' in row else None
        existing_entry.requested_by_id = clean_data(row['requested_by_id']) if 'requested_by_id' in row else None
    else:
        new_entry_args = {
            'id': doc_id,
            'client_id': client.id,
            'job_link': clean_data(job_link) if 'job_link' in row else None,
            'job_title': row['Título'],
            'project': clean_data(row['Projeto']) if 'Projeto' in row else None,
            'job_creation_date': clean_data(job_creation_date),
            'job_start_date': clean_data(job_start_date),
            'job_finish_date': clean_data(job_finish_date),
            'job_status': clean_data(row['Status']),
            'job_category': categoria.value,  
            'delivery_category': map_category_to_delivery_category(categoria).value,
            'user_in_charge_id': clean_data(row['Responsável']) if 'Responsável' in row else None,
            'project': clean_data(row['Projeto']) if 'Projeto' in row else None,
            'job_link': clean_data(job_link) if 'job_link' in row else None,
            'delivery_control_category': clean_data(row['delivery_control_category']) if 'delivery_control_category' in row else None,
            'job_deadline_date': clean_data(row['job_deadline_date']) if 'job_deadline_date' in row else None,
            'updated_by_id': clean_data(row['updated_by_id']) if 'updated_by_id' in row else None,
            'next_month_plan_sent': clean_data(row['next_month_plan_sent']) if 'next_month_plan_sent' in row else None,
            'next_month_plant_sent_date': clean_data(row['next_month_plant_sent_date']) if 'next_month_plant_sent_date' in row else None,
            'requested_by_id': clean_data(row['requested_by_id']) if 'requested_by_id' in row else None,
            'used_mandalecas': mandalecas
        }

        logging.info(f"Criando nova entrada em DeliveryControl com ID {doc_id}. Campo used_mandalecas definido como {mandalecas}.")
        
        new_entry = DeliveryControl(**new_entry_args)
        session.add(new_entry)

    session.commit()
    logging.info(f"Dados comitados para DeliveryControl com ID {doc_id}.")

def process_jobs(df, client_name_map, job_category_map, session):
    logging.info(f"Iniciando processamento dos trabalhos. Número de linhas a processar: {len(df)}")

    for index, row in df.iterrows():
        client_name = row['Cliente'].strip()
        client = client_name_map.get(index)
        
        if not client:
            logging.info(f"Cliente não encontrado: {client_name}")
            continue
        
        title = row['Título']

        # Verifica a categoria do trabalho
        category = job_category_map.get(index)
        if not category:
            logging.info(f"Título não correspondente: {title}")
            continue

        delivery_category = map_category_to_delivery_category(category)
        if not delivery_category:
            logging.info(f"Categoria de entrega não correspondente para o título: {title}")
            continue

        doc_id = int(str(row['Nº Doc']).split('.')[0])
        
        # Extraindo mandalecas
        mandalecas = extract_mandalecas(title)
        if mandalecas is None:
            logging.info(f"Mandalecas não encontradas no título: {title}")
            continue
        
        # Verifica se o ID já existe
        existing_entry = session.query(DeliveryControl).filter_by(id=doc_id).first()
        if existing_entry:
            logging.info(f"ID {doc_id} já existe. Atualizando a entrada existente.")
            upsert_delivery_control(session, doc_id, client, row, job_link=row.get('job_link', None), 
                                    mandalecas=mandalecas, job_creation_date=row['Data de criação'], 
                                    job_start_date=row['Data Início'], job_finish_date=row['Data de Conclusão'], 
                                    categoria=category)
        else:
            # Atualiza o banco de dados
            new_delivery = DeliveryControl(
                id=doc_id,
                client_id=client.id,
                job_title=title,
                job_category=category,
                delivery_category=delivery_category,
                job_creation_date=clean_data(row['Data de criação']),
                job_start_date=clean_data(row['Data Início']),
                job_finish_date=clean_data(row['Data de Conclusão']),
                job_status=clean_data(row['Status']),
                user_in_charge_id=clean_data(row['Responsável']) if 'Responsável' in row else None,
                project=clean_data(row['Projeto']) if 'Projeto' in row else None,
                job_link=clean_data(row['job_link']) if 'job_link' in row else None,
                delivery_control_category=clean_data(row['delivery_control_category']) if 'delivery_control_category' in row else None,
                job_deadline_date=clean_data(row['job_deadline_date']) if 'job_deadline_date' in row else None,
                updated_by_id=clean_data(row['updated_by_id']) if 'updated_by_id' in row else None,
                next_month_plan_sent=clean_data(row['next_month_plan_sent']) if 'next_month_plan_sent' in row else None,
                next_month_plant_sent_date=clean_data(row['next_month_plant_sent_date']) if 'next_month_plant_sent_date' in row else None,
                requested_by_id=clean_data(row['requested_by_id']) if 'requested_by_id' in row else None
            )

            session.add(new_delivery)

    session.commit()
    logging.info("Processamento de trabalhos concluído.")
    session.close()

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
    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.CRIACAO)
    mandalecas_usadas_adaptacao = sum((entrega.used_format_adaptation_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.ADAPTACAO)
    mandalecas_usadas_conteudo = sum((entrega.used_content_production_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.CONTENT_PRODUCTION)
    mandalecas_usadas_stories_instagram = sum((entrega.used_stories_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STORIES_INSTAGRAM)
    mandalecas_usadas_feed_linkedin = sum((entrega.used_feed_linkedin_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_LINKEDIN)
    mandalecas_usadas_feed_tiktok = sum((entrega.used_feed_tiktok_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_TIKTOK)
    mandalecas_usadas_stories_repost_instagram = sum((entrega.used_stories_repost_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STORIES_REPOST_INSTAGRAM)
    mandalecas_usadas_feed_instagram = sum((entrega.used_feed_instagram_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.FEED_INSTAGRAM)
    mandalecas_usadas_static_trafego_pago = sum((entrega.used_static_trafego_pago_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.STATIC_TRAFEGO_PAGO)
    mandalecas_usadas_animated_trafego_pago = sum((entrega.used_animated_trafego_pago_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == JobCategoryEnum.ANIMATED_TRAFEGO_PAGO)

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
    session.close()  # Fecha a sessão após commit

def read_excel_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    
    df.dropna(how='all', inplace=True)
    df.dropna(subset=['Nº Doc', 'Título'], inplace=True)

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
    initialize_session_state()
    session = Session()

    df = pd.read_excel(file)
    st.session_state.df = df

    logging.info(f"Arquivo XLSX lido com sucesso. Colunas: {list(df.columns)}")

    # Adicionando log para número de linhas antes da remoção de NaN
    logging.info(f"Número de linhas antes da remoção de NaN: {len(df)}")

    # Limpeza dos dados
    df.dropna(how='all', inplace=True)
    df.dropna(subset=['Nº Doc', 'Título'], inplace=True)

    df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # Adicionando log para número de linhas após a remoção de NaN
    logging.info(f"Número de linhas após a remoção de NaN: {len(df)}")

    st.session_state.df = df

    client_name_map = {}
    clients_to_add = []

    for index, row in df.iterrows():
        client_name = row['Cliente']
        client = session.query(Client).filter_by(name=client_name).first()
        if client:
            client_name_map[index] = client
        else:
            clients_to_add.append(client_name)

    if clients_to_add:
        st.session_state.clientes_nao_correspondidos = clients_to_add
        logging.info(f"Clientes não correspondidos: {clients_to_add}")
        st.stop()
    else:
        logging.info("Todos os clientes foram correspondidos com sucesso.")
    
    job_category_map = {}
    unmatched_categories = []

    for index, row in df.iterrows():
        categoria = identificar_categoria(row['Título'], row['Projeto'])
        if categoria:
            job_category_map[index] = categoria
            logging.info(f"Categoria identificada para título '{row['Título']}']: {categoria}")
        else:
            unmatched_categories.append(row['Título'])

    if unmatched_categories:
        st.session_state.unmatched_categories = unmatched_categories
        logging.info(f"Categorias não correspondidas: {unmatched_categories}")
        st.stop()
    else:
        logging.info("Todas as categorias foram correspondidas com sucesso.")

    st.session_state.client_name_map = client_name_map
    st.session_state.job_category_map = job_category_map

    process_jobs(df, client_name_map, job_category_map, session)

    st.success("Arquivo processado com sucesso!")
