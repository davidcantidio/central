import re
import streamlit as st
from utils import check_plan_status
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
import plotly.express as px
import plotly.graph_objects as go

# Configura o log
logging.basicConfig(
    filename='process_xlsx.log',  # Nome do arquivo de log
    level=logging.INFO,           # Nível de log (INFO para registrar informações úteis)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato das mensagens de log
    datefmt='%Y-%m-%d %H:%M:%S'   # Formato da data e hora
)

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()

def map_category_to_delivery_category(category):
    if category in [
        JobCategoryEnum.REELS_INSTAGRAM,
        JobCategoryEnum.CAROUSEL_INSTAGRAM,
        JobCategoryEnum.CARD_INSTAGRAM,
        JobCategoryEnum.STORIES_INSTAGRAM,
        JobCategoryEnum.FEED_INSTAGRAM,
        JobCategoryEnum.FEED_LINKEDIN,
        JobCategoryEnum.FEED_TIKTOK,
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM
    ]:
        return DeliveryCategoryEnum.REDES_SOCIAIS
    elif category in [
        JobCategoryEnum.CRIACAO,
        JobCategoryEnum.ADAPTACAO,
        JobCategoryEnum.CONTENT_PRODUCTION
    ]:
        return DeliveryCategoryEnum.CRIACAO
    elif category in [
        JobCategoryEnum.STATIC_TRAFEGO_PAGO,
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO
    ]:
        return DeliveryCategoryEnum.TRAFEGO_PAGO
    else:
        return None


def create_timeline_chart(today, deadline_date, plan_sent_date):
    # Lista de dias do mês
    days_in_month = [date for date in pd.date_range(start=today.replace(day=1), end=today.replace(day=28) + pd.offsets.MonthEnd(1))]
    x_values = [day.strftime('%Y-%m-%d') for day in days_in_month]

    # Posicionando os eventos
    event_dates = [today.strftime('%Y-%m-%d'), deadline_date.strftime('%Y-%m-%d')]
    event_labels = ["Hoje", "Prazo"]
    event_colors = ["blue", "red"]

    if plan_sent_date:
        event_dates.append(plan_sent_date.strftime('%Y-%m-%d'))
        event_labels.append("Plano Enviado")
        event_colors.append("green")

    # Criar a linha do tempo
    fig = go.Figure()

    # Adicionar os dias do mês na linha do tempo
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[1] * len(x_values),
        mode='lines+markers',
        line=dict(color='lightgrey', width=2),
        marker=dict(color='lightgrey', size=6),
        showlegend=False,
        hoverinfo='x'
    ))

    # Adicionar os eventos na linha do tempo
    for date, label, color in zip(event_dates, event_labels, event_colors):
        fig.add_trace(go.Scatter(
            x=[date],
            y=[1],
            mode='markers+text',
            marker=dict(color=color, size=12),
            text=[label],
            textposition='top center',
            showlegend=False,
            hoverinfo='x+text'
        ))

    fig.update_layout(
        title="Linha do Tempo do Plano Mensal",
        xaxis=dict(
            tickmode='array',
            tickvals=x_values,
            ticktext=[day.strftime('%d') for day in days_in_month]
        ),
        yaxis=dict(visible=False),
        showlegend=False,
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

def display_client_plan_status():
    clientes_df = pd.read_sql_query("SELECT * FROM clients", engine)
    cliente_id = st.selectbox("Selecione o Cliente", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])
    
    with Session(bind=engine) as session:
        client = session.query(Client).filter(Client.id == cliente_id).first()
        delivery_controls = session.query(DeliveryControl).filter(DeliveryControl.client_id == cliente_id).all()
        
        plan_status, plan_sent_date = check_plan_status(client, delivery_controls)
        
        st.write(f"Status do Plano: {plan_status}")
        
        today = datetime.today()
        deadline_date = datetime(today.year, today.month, client.monthly_plan_deadline_day)
        
        # Imprimir na tela as datas para debug
        st.write(f"Dia Atual: {today.strftime('%Y-%m-%d')}")
        st.write(f"Dia do Deadline: {deadline_date.strftime('%Y-%m-%d')}")
        if plan_sent_date:
            st.write(f"Dia do Envio do Plano: {plan_sent_date.strftime('%Y-%m-%d')}")
            st.write(f"Data de Envio: {plan_sent_date.strftime('%Y-%m-%d')}")
        else:
            st.write("Plano não enviado.")

        fig = create_timeline_chart(today, deadline_date, plan_sent_date)
        st.plotly_chart(fig)
        
        if st.button("Confirmar Envio de Plano"):
            plan_sent_date = st.date_input("Selecione a Data de Envio", value=today)
            if st.button("Salvar Data de Envio"):
                with Session(bind=engine) as session:
                    delivery_control = session.query(DeliveryControl).filter(DeliveryControl.client_id == cliente_id).first()
                    if delivery_control:
                        delivery_control.next_month_plan_sent = True
                        delivery_control.next_month_plant_sent_date = plan_sent_date
                        session.commit()
                        st.success("Data de envio do plano atualizada com sucesso.")

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
                delivery_category,
                used_reels_instagram_mandalecas,
                used_carousel_mandalecas,
                used_card_instagram_mandalecas
            FROM delivery_control
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id, start_date, end_date))
    logging.info(f"Dados obtidos: {df.shape[0]} registros encontrados")
    return df

def debug_display_data(client_id, mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, selected_delivery_categories):
    logging.info("Exibindo dados para debug.")
    try:
        mandalecas_contratadas[JobCategoryEnum.FEED_INSTAGRAM] += mandalecas_contratadas.pop(JobCategoryEnum.REELS_INSTAGRAM, 0)
        mandalecas_usadas[JobCategoryEnum.FEED_INSTAGRAM] += mandalecas_usadas.pop(JobCategoryEnum.REELS_INSTAGRAM, 0)
        mandalecas_acumuladas[JobCategoryEnum.FEED_INSTAGRAM] += mandalecas_acumuladas.pop(JobCategoryEnum.REELS_INSTAGRAM, 0)

        category_gauges = {}
        social_media_data = {
            "Carrossel Instagram": mandalecas_usadas.get(JobCategoryEnum.CAROUSEL_INSTAGRAM, 0),
            "Reels Instagram": mandalecas_usadas.get(JobCategoryEnum.REELS_INSTAGRAM, 0),
            "Card Instagram": mandalecas_usadas.get(JobCategoryEnum.CARD_INSTAGRAM, 0)
        }

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

            if delivery_category == DeliveryCategoryEnum.REDES_SOCIAIS:
                pie_chart = create_pie_chart(social_media_data, "Distribuição Redes Sociais")
                st.plotly_chart(pie_chart)

    except KeyError as e:
        logging.error(f"Erro ao exibir os dados: {e}")
        st.error(f"Erro ao exibir os dados: {e}")

def create_pie_chart(data, title):
    # Filtra valores nulos ou zero para não exibir fatias vazias
    data = {k: v for k, v in data.items() if v > 0}
    labels = list(data.keys())
    values = list(data.values())

    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_layout(title_text=title)

    return fig

def get_last_month_date_range():
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)
    return first_day_of_last_month, last_day_of_last_month

# Função principal da página de criação (Entregas)
def page_criacao():
    st.title("Entregas")
    display_client_plan_status()

    with st.sidebar:
        st.header("Filtro de Cliente e Data")
        clientes_df = pd.read_sql_query("SELECT * FROM clients", engine)
        cliente_id = st.selectbox("Selecione o Cliente", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0], key='unique_select_box_id_1')

        first_day_of_last_month, last_day_of_last_month = get_last_month_date_range()

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data de início", value=first_day_of_last_month, key="data_inicio")
        with col2:
            data_fim = st.date_input("Data de fim", value=last_day_of_last_month, key="data_fim")

        st.session_state["cliente_id"] = cliente_id

        uploaded_file = st.file_uploader("Upload de arquivo XLSX", type=["xlsx"], key="unique_file_uploader_key")
        if uploaded_file:
            logging.info("Arquivo XLSX enviado. Iniciando processamento...")
            try:
                process_xlsx_file(uploaded_file)
                st.success("Arquivo processado com sucesso e dados inseridos no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                logging.error(f"Erro ao processar o arquivo: {e}", exc_info=True)

        delivery_data = get_delivery_control_data(cliente_id, data_inicio, data_fim)

        mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

        st.header("Selecione as Categorias de Entrega")
        selected_delivery_categories = []
        for delivery_category in DeliveryCategoryEnum:
            if st.checkbox(delivery_category.value, value=True):
                selected_delivery_categories.append(delivery_category)

    debug_display_data(cliente_id, mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, selected_delivery_categories)

def calcular_mandalecas(cliente_id):
    with Session(bind=engine) as session:
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
            JobCategoryEnum.FEED_INSTAGRAM: client.n_monthly_contracted_feed_instagram_mandalecas  # Ajustar esta linha para somar corretamente
        }

        mandalecas_usadas = {
            JobCategoryEnum.CRIACAO: sum(job.used_creative_mandalecas for job in client.delivery_controls if job.used_creative_mandalecas is not None),
            JobCategoryEnum.ADAPTACAO: sum(job.used_format_adaptation_mandalecas for job in client.delivery_controls if job.used_format_adaptation_mandalecas is not None),
            JobCategoryEnum.CONTENT_PRODUCTION: sum(job.used_content_production_mandalecas for job in client.delivery_controls if job.used_content_production_mandalecas is not None),
            JobCategoryEnum.STORIES_INSTAGRAM: sum(job.used_stories_instagram_mandalecas for job in client.delivery_controls if job.used_stories_instagram_mandalecas is not None),
            JobCategoryEnum.FEED_LINKEDIN: sum(job.used_feed_linkedin_mandalecas for job in client.delivery_controls if job.used_feed_linkedin_mandalecas is not None),
            JobCategoryEnum.FEED_TIKTOK: sum(job.used_feed_tiktok_mandalecas for job in client.delivery_controls if job.used_feed_tiktok_mandalecas is not None),
            JobCategoryEnum.STORIES_REPOST_INSTAGRAM: sum(job.used_stories_repost_instagram_mandalecas for job in client.delivery_controls if job.used_stories_repost_instagram_mandalecas is not None),
            JobCategoryEnum.STATIC_TRAFEGO_PAGO: sum(job.used_static_trafego_pago_mandalecas for job in client.delivery_controls if job.used_static_trafego_pago_mandalecas is not None),
            JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: sum(job.used_animated_trafego_pago_mandalecas for job in client.delivery_controls if job.used_animated_trafego_pago_mandalecas is not None),
            JobCategoryEnum.FEED_INSTAGRAM: sum(job.used_reels_instagram_mandalecas + job.used_carousel_mandalecas + job.used_card_instagram_mandalecas for job in client.delivery_controls if job.used_reels_instagram_mandalecas is not None)  # Ajustar esta linha para somar corretamente
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
            JobCategoryEnum.FEED_INSTAGRAM: client.accumulated_feed_instagram_mandalecas  # Ajustar esta linha para somar corretamente
        }

    return mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas
