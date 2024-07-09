import re
import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControl, Client, Users, JobCategoryEnum
from common.database import engine
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from process_xlsx import process_jobs, identificar_categoria, extract_mandalecas
import logging

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
        }))

    # Atualizar layout para lidar com valores que excedem o limite
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[
            dict(
                x=0.5, y=0.55, xref='paper', yref='paper',
                text="Valor atual",
                showarrow=False
            ),
            dict(
                x=0.5, y=0, xref='paper', yref='paper',
                text=f"Acumulado: {accumulated}",
                showarrow=False,
                font=dict(color="gray", size=12)
            )
        ]
    )

    return fig

def debug_display_data(cliente_id=None, start_date=None, end_date=None):
    logging.info("Executando debug_display_data...")
    try:
        if cliente_id:
            clients = session.query(Client).filter_by(id=cliente_id).all()
        else:
            clients = session.query(Client).all()

        for client in clients:
            entregas_creative = session.query(DeliveryControl).filter(
                DeliveryControl.client_id == client.id,
                DeliveryControl.job_creation_date >= start_date,
                DeliveryControl.job_creation_date <= end_date
            ).all()

            mandalecas_usadas = {category: 0 for category in JobCategoryEnum}
            mandalecas_contratadas = {
                JobCategoryEnum.CRIACAO: client.n_monthly_contracted_creative_mandalecas,
                JobCategoryEnum.ADAPTACAO: client.n_monthly_contracted_format_adaptation_mandalecas,
                JobCategoryEnum.CONTENT_PRODUCTION: client.n_monthly_contracted_content_production_mandalecas,
                JobCategoryEnum.STORIES_INSTAGRAM: client.n_monthly_contracted_stories_instagram_mandalecas,
                JobCategoryEnum.FEED_LINKEDIN: client.n_monthly_contracted_feed_linkedin_mandalecas,
                JobCategoryEnum.FEED_TIKTOK: client.n_monthly_contracted_feed_tiktok_mandalecas,
                JobCategoryEnum.STORIES_REPOST_INSTAGRAM: client.n_monthly_contracted_stories_repost_instagram_mandalecas,
                JobCategoryEnum.REELS_INSTAGRAM: client.n_monthly_contracted_reels_instagram_mandalecas,
                JobCategoryEnum.FEED_INSTAGRAM: client.n_monthly_contracted_feed_instagram_mandalecas,
                JobCategoryEnum.STORIES: 0,  # Placeholder para categorias adicionais
                JobCategoryEnum.PRODUCAO: 0,  # Placeholder para categorias adicionais
                JobCategoryEnum.TRAFEGO_PAGO: 0  # Placeholder para categorias adicionais
            }
            mandalecas_acumuladas = {category: 0 for category in JobCategoryEnum}

            for entrega in entregas_creative:
                categoria = identificar_categoria(entrega.job_title, entrega.project)
                if categoria in mandalecas_usadas:
                    mandalecas_usadas[categoria] += entrega.used_creative_mandalecas
                if categoria in mandalecas_acumuladas:
                    mandalecas_acumuladas[categoria] = client.accumulated_creative_mandalecas  # Ajustar conforme necessário

            gauges = []
            for category in JobCategoryEnum:
                if mandalecas_contratadas[category] > 0:
                    gauges.append(display_gauge_chart(
                        category.value,
                        mandalecas_contratadas[category],
                        mandalecas_usadas[category],
                        mandalecas_acumuladas[category]
                    ))

            # Exibir os gauges em linhas com até 3 colunas
            for i in range(0, len(gauges), 3):
                cols = st.columns(3)
                for col, fig in zip(cols, gauges[i:i+3]):
                    col.plotly_chart(fig)

    except Exception as e:
        logging.error(f"Erro ao exibir os dados: {e}", exc_info=True)
        st.write(f"Erro ao exibir os dados: {e}")

def get_last_month_date_range():
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)
    return first_day_of_last_month, last_day_of_last_month

# Função principal da página de criação (Entregas)
def page_criacao():
    st.title("Entregas")

    # Seleção do cliente
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

    # Exibir debug data para o cliente selecionado e intervalo de datas
    debug_display_data(cliente_id, data_inicio, data_fim)
