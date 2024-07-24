import re
import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControl, Client, Users, JobCategoryEnum, DeliveryCategoryEnum
from common.database import engine
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import sqlite3
from process_xlsx import identificar_categoria, process_xlsx_file

# Configura o log
logging.basicConfig(
    filename='process_xlsx.log',  # Nome do arquivo de log
    level=logging.INFO,           # Nível de log (INFO para registrar informações úteis)
    format='%(asctime)s - %(levellevel)s - %(message)s',  # Formato das mensagens de log
    datefmt='%Y-%m-%d %H:%M:%S'   # Formato da data e hora
)

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()


def display_gauge_chart(title, contracted, used, accumulated=0):
    max_value = contracted + accumulated
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=used,
        title={'text': title},
        gauge={
            'axis': {'range': [0, max_value]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, contracted], 'color': "lightgray"},
                {'range': [contracted, max_value], 'color': "orange"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': contracted
            }
        }
    ))

    # Atualizar layout para lidar com valores que excedem o limite
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[
            dict(
                x=0.5, y=0, xref='paper', yref='paper',
                text=f"Acumulado: {accumulated}",
                showarrow=False,
                font=dict(color="gray", size=12)
            )
        ]
    )

    return fig


def get_delivery_control_data(cliente_id, start_date, end_date):
    logging.info(f"Obtendo dados de DeliveryControl para o cliente ID {cliente_id} entre {start_date} e {end_date}")
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        query = """
            SELECT 
                job_link, 
                project, 
                job_category, 
                job_creation_date,
                delivery_category
            FROM delivery_control
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id, start_date, end_date))
    logging.info(f"Dados obtidos: {df.shape[0]} registros encontrados")
    return df

def debug_display_data(client, mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, selected_delivery_categories):
    logging.info("Exibindo dados para debug.")
    try:
        mandalecas_contratadas[JobCategoryEnum.FEED_INSTAGRAM] += mandalecas_contratadas.pop(JobCategoryEnum.REELS_INSTAGRAM, 0)
        mandalecas_usadas[JobCategoryEnum.FEED_INSTAGRAM] += mandalecas_usadas.pop(JobCategoryEnum.REELS_INSTAGRAM, 0)
        mandalecas_acumuladas[JobCategoryEnum.FEED_INSTAGRAM] += mandalecas_acumuladas.pop(JobCategoryEnum.REELS_INSTAGRAM, 0)

        category_gauges = {}
        
        for category in JobCategoryEnum:
            delivery_category = map_category_to_delivery_category(category)
            if (mandalecas_contratadas.get(category, 0) > 0 or 
                mandalecas_usadas.get(category, 0) > 0 or 
                mandalecas_acumuladas.get(category, 0) > 0) and delivery_category in selected_delivery_categories:
                
                if delivery_category not in category_gauges:
                    category_gauges[delivery_category] = []

                gauge_chart = display_gauge_chart(
                    title=category.value,
                    contracted=mandalecas_contratadas.get(category, 0),
                    used=mandalecas_usadas.get(category, 0),
                    accumulated=mandalecas_acumuladas.get(category, 0)
                )
                category_gauges[delivery_category].append(gauge_chart)

        for delivery_category, gauges in category_gauges.items():
            st.subheader(delivery_category.value)
            cols = st.columns(3)
            for i, gauge in enumerate(gauges):
                with cols[i % 3]:
                    st.plotly_chart(gauge)

    except KeyError as e:
        logging.error(f"Erro ao exibir os dados: {e}")
        st.error(f"Erro ao exibir os dados: {e}")



def get_last_month_date_range():
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)
    return first_day_of_last_month, last_day_of_last_month

# Função principal da página de criação (Entregas)
def page_criacao():
    st.title("Entregas")

    # Seleção do cliente no menu lateral
    with st.sidebar:
        st.header("Filtro de Cliente e Data")
        clientes_df = pd.read_sql_query("SELECT * FROM clients", engine)
        cliente_id = st.selectbox("Selecione o Cliente", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])

        # Obter as datas padrão do mês passado
        first_day_of_last_month, last_day_of_last_month = get_last_month_date_range()

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data de início", value=first_day_of_last_month, key="data_inicio")
        with col2:
            data_fim = st.date_input("Data de fim", value=last_day_of_last_month, key="data_fim")

        st.session_state["cliente_id"] = cliente_id

        # Upload do arquivo XLSX na barra lateral
        uploaded_file = st.file_uploader("Upload de arquivo XLSX", type=["xlsx"], key="unique_file_uploader_key")
        if uploaded_file:
            logging.info("Arquivo XLSX enviado. Iniciando processamento...")
            try:
                process_xlsx_file(uploaded_file)
                st.success("Arquivo processado com sucesso e dados inseridos no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                logging.error(f"Erro ao processar o arquivo: {e}", exc_info=True)

        # Obter dados do DeliveryControl
        delivery_data = get_delivery_control_data(cliente_id, data_inicio, data_fim)

        # Calcular mandalecas contratadas, usadas e acumuladas
        mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

        # Exibir caixas de seleção para categorias de entrega
        st.header("Selecione as Categorias de Entrega")
        selected_delivery_categories = []
        for delivery_category in DeliveryCategoryEnum:
            if st.checkbox(delivery_category.value, value=True):
                selected_delivery_categories.append(delivery_category)

    # Exibir debug data para o cliente selecionado e intervalo de datas
    debug_display_data(cliente_id, mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, selected_delivery_categories)

def calcular_mandalecas(cliente_id):
    session = Session()
    client = session.query(Client).filter(Client.id == cliente_id).first()

    mandalecas_contratadas = {
        JobCategoryEnum.CRIACAO: client.n_monthly_contracted_creative_mandalecas,
        JobCategoryEnum.ADAPTACAO: client.n_monthly_contracted_format_adaptation_mandalecas,
        JobCategoryEnum.CONTENT_PRODUCTION: client.n_monthly_contracted_content_production_mandalecas,
        JobCategoryEnum.STORIES_INSTAGRAM: client.n_monthly_contracted_stories_instagram_mandalecas,
        JobCategoryEnum.FEED_LINKEDIN: client.n_monthly_contracted_feed_linkedin_mandalecas,
        JobCategoryEnum.FEED_TIKTOK: client.n_monthly_contracted_feed_tiktok_mandalecas,
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM: client.n_monthly_contracted_stories_repost_instagram_mandalecas,
        JobCategoryEnum.STATIC_TRAFEGO_PAGO: client.n_monthly_contracted_trafego_pago_static,
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: client.n_monthly_contracted_trafego_pago_animated,
        JobCategoryEnum.FEED_INSTAGRAM: 0  # Ajustar esta linha para somar corretamente
    }

    mandalecas_usadas = {
        JobCategoryEnum.CRIACAO: sum((entrega.used_creative_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.ADAPTACAO: sum((entrega.used_format_adaptation_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.CONTENT_PRODUCTION: sum((entrega.used_content_production_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.STORIES_INSTAGRAM: sum((entrega.used_stories_instagram_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.FEED_LINKEDIN: sum((entrega.used_feed_linkedin_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.FEED_TIKTOK: sum((entrega.used_feed_tiktok_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM: sum((entrega.used_stories_repost_instagram_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.STATIC_TRAFEGO_PAGO: sum((entrega.used_static_trafego_pago_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: sum((entrega.used_animated_trafego_pago_mandalecas or 0) for entrega in client.delivery_controls),
        JobCategoryEnum.FEED_INSTAGRAM: sum((entrega.used_carousel_mandalecas or 0) + (entrega.used_card_instagram_mandalecas or 0) + (entrega.used_reels_instagram_mandalecas or 0) for entrega in client.delivery_controls),
    }

    mandalecas_acumuladas = {
        JobCategoryEnum.CRIACAO: client.accumulated_creative_mandalecas,
        JobCategoryEnum.ADAPTACAO: client.accumulated_format_adaptation_mandalecas,
        JobCategoryEnum.CONTENT_PRODUCTION: client.accumulated_content_production_mandalecas,
        JobCategoryEnum.STORIES_INSTAGRAM: client.accumulated_stories_instagram_mandalecas,
        JobCategoryEnum.FEED_LINKEDIN: client.accumulated_feed_linkedin_mandalecas,
        JobCategoryEnum.FEED_TIKTOK: client.accumulated_feed_tiktok_mandalecas,
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM: client.accumulated_stories_repost_instagram_mandalecas,
        JobCategoryEnum.STATIC_TRAFEGO_PAGO: client.accumulated_trafego_pago_static,
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: client.accumulated_trafego_pago_animated,
        JobCategoryEnum.FEED_INSTAGRAM: client.accumulated_feed_instagram_mandalecas,
    }

    session.close()
    return mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas

def map_category_to_delivery_category(job_category):
    mapping = {
        JobCategoryEnum.CRIACAO: DeliveryCategoryEnum.CRIACAO,
        JobCategoryEnum.ADAPTACAO: DeliveryCategoryEnum.CRIACAO,
        JobCategoryEnum.CONTENT_PRODUCTION: DeliveryCategoryEnum.CONTENT_PRODUCTION,
        JobCategoryEnum.STORIES_INSTAGRAM: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.FEED_LINKEDIN: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.FEED_TIKTOK: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.FEED_INSTAGRAM: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.STATIC_TRAFEGO_PAGO: DeliveryCategoryEnum.TRAFEGO_PAGO,
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: DeliveryCategoryEnum.TRAFEGO_PAGO
    }
    return mapping.get(job_category)
