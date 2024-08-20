import re
import streamlit as st
from utils import check_plan_status
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControl, Client, Users, JobCategoryEnum, DeliveryCategoryEnum, RedesSociaisPlan, RedesSociaisPlanStatusEnum
from common.database import engine
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import sqlite3
from process_xlsx import identificar_categoria, process_xlsx_file
import plotly.express as px
from sqlalchemy.sql import func
import calendar
import locale

from streamlit_modal import Modal
from datetime import datetime


# Configurar localidade para português
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# load_css("assets/style.css")

# Configura o log
logging.basicConfig(
    filename='page_criacao_logic.log',  # Nome do arquivo de log
    level=logging.DEBUG,  # Nível de log (DEBUG para registrar informações detalhadas)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato das mensagens de log
    datefmt='%Y-%m-%d %H:%M:%S'  # Formato da data e hora
)

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()

def editar_data_envio_plano(cliente_id):
    plan_sent_date = st.session_state['date_input']
    if plan_sent_date:
        try:
            salvar_data_envio_plano(cliente_id, plan_sent_date)
            st.session_state['edit_date'] = False  # Fecha o input de data após a edição
            st.success(f"Data de envio atualizada para {plan_sent_date.strftime('%d/%m/%Y')}")
        except Exception as e:
            st.error(f"Erro ao atualizar a data de envio: {e}")
            logging.error(f"Erro ao atualizar a data de envio: {e}")

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
    days_in_month = [date for date in pd.date_range(start=today.replace(day=1), end=today.replace(day=28) + pd.offsets.MonthEnd(1))]
    x_values = [day.strftime('%Y-%m-%d') for day in days_in_month]

    event_dates = [deadline_date.strftime('%Y-%m-%d')]
    event_colors = ["red"]
    event_texts = ["Deadline"]

    if plan_sent_date:
        event_dates.append(plan_sent_date.strftime('%Y-%m-%d'))
        event_colors.append("green")
        event_texts.append("Enviado")

    # Criando a figura
    fig = go.Figure()

    # Adicionando a linha do tempo com os dias do mês
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[1] * len(x_values),
        mode='lines+markers',
        line=dict(color='lightgrey', width=2),
        marker=dict(color='lightgrey', size=6),
        hoverinfo='x',
        showlegend=False  # Não mostrar na legenda principal
    ))

    # Adicionando os eventos com as legendas
    for date, color, text in zip(event_dates, event_colors, event_texts):
        text_position = "top center" if text == "Enviado" else "bottom center"
        fig.add_trace(go.Scatter(
            x=[date],
            y=[1],
            mode='markers+text',
            marker=dict(color=color, size=12),
            text=[text],
            textposition=text_position,
            showlegend=False,
            hoverinfo='none'
        ))

    # Configurações gerais do layout
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=x_values,
            ticktext=[day.strftime('%d') for day in days_in_month],
            showline=False,
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=10),
            tickangle=0,
            ticks='outside',
            ticklen=4,
            tickwidth=1,
        ),
        yaxis=dict(visible=False),
        height=150,
        margin=dict(l=20, r=20, t=10, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    return fig

def display_client_header(client, title):
    st.subheader(f"{client.name} - {title}")

def display_send_plan_modal(cliente_id):
    modal = Modal("Data de Envio do Plano", key="enviar-plano-modal", max_width=800)
    
    # Botão para abrir o modal
    if st.button("Enviar Plano"):
        modal.open()

    if modal.is_open():
        with modal.container():
            st.write("Selecione a Data de Envio do Plano")
            selected_date = st.date_input("Data de Envio", value=datetime.today(), key="date_input_modal")

            if st.button("Confirmar", key="confirmar_button_modal"):
                salvar_data_envio_plano(cliente_id, selected_date)
                st.session_state['plan_sent_date'] = selected_date
                st.experimental_rerun()

def display_plan_sent_date(cliente_id):
    # Inicialize 'edit_date' se não estiver presente no session_state
    if 'edit_date' not in st.session_state:
        st.session_state['edit_date'] = False

    # Verifique se a data de envio do plano está presente
    if st.session_state['plan_sent_date']:
        if st.session_state['edit_date']:
            plan_sent_date = st.date_input("Edite a Data de Envio", value=st.session_state['plan_sent_date'], key="date_input")
        else:
            if st.button(st.session_state['plan_sent_date'].strftime('%d/%m/%Y'), key="edit_date_button"):
                st.session_state['edit_date'] = True

        if st.session_state['edit_date'] and st.button("Salvar Data de Envio"):
            editar_data_envio_plano(cliente_id)
            st.session_state['edit_date'] = False

def render_timeline_chart(today, deadline_date, plan_sent_date):
    fig = create_timeline_chart(today, deadline_date, plan_sent_date)
    st.plotly_chart(fig, use_container_width=True)

def display_client_plan_status():
    cliente_id = st.session_state.get("cliente_id")
    with Session(bind=engine) as session:
        client = session.query(Client).filter(Client.id == cliente_id).first()
        redes_sociais_plan = session.query(RedesSociaisPlan).filter(RedesSociaisPlan.client_id == cliente_id).first()

        if redes_sociais_plan:
            plan_status = determinar_status_plano(client, redes_sociais_plan)
            if 'plan_sent_date' not in st.session_state or not st.session_state['plan_sent_date']:
                st.session_state['plan_sent_date'] = redes_sociais_plan.send_date
        else:
            plan_status = "Plano não encontrado"
            st.session_state['plan_sent_date'] = None

        next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B')
        title = f"Planejamento Redes Sociais: {next_month.capitalize()}"

        today = datetime.today()
        deadline_date = datetime(today.year, today.month, client.monthly_plan_deadline_day)

        # Exibir título e informações do cliente
        display_client_header(client, title)

        # Exibir botão e modal para envio do plano
        display_send_plan_modal(cliente_id)

        # Exibir data de envio do plano e permitir edição
        display_plan_sent_date(cliente_id)

        # Renderizar gráfico de linha do tempo
        render_timeline_chart(today, deadline_date, st.session_state['plan_sent_date'])

def confirmar_envio_plano(cliente_id):
    logging.info(f"Botão 'Enviar' pressionado para o cliente ID {cliente_id}.")
    st.session_state['confirm_plan_send'] = True
    st.session_state['plan_sent_date'] = datetime.today()
    st.rerun()

def determinar_status_plano(cliente, plano):
    hoje = datetime.today().date()  # Converter para datetime.date
    prazo = datetime(hoje.year, hoje.month, cliente.monthly_plan_deadline_day).date()  # Converter para datetime.date
    logging.info(f"Data de hoje: {hoje}, Prazo: {prazo}")

    if plano is None or plano.send_date is None:
        logging.info("Plano ainda não foi enviado.")
        if hoje > prazo:
            return RedesSociaisPlanStatusEnum.DELAYED
        else:
            return RedesSociaisPlanStatusEnum.AWAITING
    else:
        send_date = plano.send_date
        if isinstance(send_date, datetime):
            send_date = send_date.date()
        logging.info(f"Plano enviado em: {send_date}")
        if send_date <= prazo:
            return RedesSociaisPlanStatusEnum.ON_TIME
        else:
            return RedesSociaisPlanStatusEnum.DELAYED

def confirmar_envio_plano(cliente_id):
    if st.button("Confirmar Envio de Plano"):
        logging.info(f"Botão 'Confirmar Envio de Plano' pressionado para o cliente ID {cliente_id}.")
        st.session_state['confirm_plan_send'] = True
        st.session_state['plan_sent_date'] = datetime.today()
        st.rerun()  # Rerun the app to ensure state is updated

    if st.session_state['confirm_plan_send']:
        plan_sent_date = st.date_input("Selecione a Data de Envio", value=st.session_state['plan_sent_date'])
        logging.info(f"Data de envio selecionada: {plan_sent_date}")

        if st.button("Salvar Data de Envio"):
            salvar_data_envio_plano(cliente_id, plan_sent_date)

def salvar_data_envio_plano(cliente_id, plan_sent_date):
    logging.info(f"Chamando salvar_data_envio_plano para cliente ID {cliente_id} com data {plan_sent_date}")
    with Session(bind=engine) as session:
        try:
            if isinstance(plan_sent_date, datetime):
                plan_sent_date = plan_sent_date.date()

            plan_month_start = plan_sent_date.replace(day=1)
            redes_sociais_plan = session.query(RedesSociaisPlan).filter(
                RedesSociaisPlan.client_id == cliente_id,
                func.strftime('%Y-%m', RedesSociaisPlan.send_date) == plan_month_start.strftime('%Y-%m')
            ).first()

            client = session.query(Client).filter(Client.id == cliente_id).first()

            if redes_sociais_plan:
                redes_sociais_plan.send_date = plan_sent_date
                redes_sociais_plan.updated_at = datetime.now()
                redes_sociais_plan.status = determinar_status_plano(client, redes_sociais_plan)
            else:
                redes_sociais_plan = RedesSociaisPlan(
                    client_id=cliente_id,
                    send_date=plan_sent_date,
                    updated_at=datetime.now(),
                    status=determinar_status_plano(client, None),
                    plan_status=RedesSociaisPlanStatusEnum.AWAITING
                )
                session.add(redes_sociais_plan)

            session.commit()
            st.success("Data de envio do plano atualizada com sucesso.")
            st.session_state['plan_sent_date'] = plan_sent_date

        except Exception as e:
            session.rollback()
            st.error(f"Erro ao atualizar a data de envio do plano: {e}")
            logging.error(f"Erro ao atualizar a data de envio do plano: {e}")

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

    fig.update_layout(
        height=220,  # Aumenta a altura do gráfico
        margin=dict(l=20, r=20, t=50, b=50),  # Aumenta a margem inferior
        annotations=[
            dict(
                x=0.5, y=0.0, xref='paper', yref='paper',
                text=f"Acumulado: {accumulated}",
                showarrow=False,
                font=dict(color="gray", size=12)
            ),
            dict(
                x=0.5, y=-0.2, xref='paper', yref='paper',  # Ajuste menor na posição Y
                text=f"Contratado: {contracted}",
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
                job_category,
                used_mandalecas
            FROM delivery_control
            WHERE client_id = ? AND job_creation_date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id, start_date, end_date))
        logging.info(f"Dados obtidos: {df}")
    logging.info(f"Dados obtidos: {df.shape[0]} registros encontrados")
    return df

def debug_display_data(cliente_id, df, mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, selected_delivery_categories):
    with Session(bind=engine) as session:
        client = session.query(Client).filter(Client.id == cliente_id).first()

        logging.info("Exibindo dados para debug.")
        try:
            logging.info(f"Mandalecas contratadas: {mandalecas_contratadas}")
            logging.info(f"Mandalecas usadas: {mandalecas_usadas}")
            logging.info(f"Mandalecas acumuladas: {mandalecas_acumuladas}")

            # Agregando os valores de used_mandalecas para as categorias específicas de redes sociais
            social_media_data = {
                "Carrossel Instagram": sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.CAROUSEL_INSTAGRAM),
                "Reels Instagram": sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.REELS_INSTAGRAM),
                "Card Instagram": sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.CARD_INSTAGRAM)
            }

            logging.info(f"Dados de redes sociais para gráfico de pizza: {social_media_data}")

            category_gauges = {
                "Instagram": [],
                "Criação": [],
                "Tráfego Pago": [],
                "Produção de Conteúdo": [],
                "Outras Redes": []
            }

            for category in JobCategoryEnum:
                delivery_category = map_category_to_delivery_category(category)
                if (mandalecas_contratadas.get(category, 0) > 0 or 
                    mandalecas_usadas.get(category, 0) > 0 or 
                    mandalecas_acumuladas.get(category, 0) > 0) and delivery_category in selected_delivery_categories:

                    gauge_chart = display_gauge_chart(
                        title=category.value,
                        contracted=mandalecas_contratadas.get(category, 0),
                        used=mandalecas_usadas.get(category, 0),
                        accumulated=mandalecas_acumuladas.get(category, 0)
                    )

                    if category in [JobCategoryEnum.FEED_INSTAGRAM, JobCategoryEnum.STORIES_INSTAGRAM]:
                        category_gauges["Instagram"].append(gauge_chart)
                    elif category in [JobCategoryEnum.CRIACAO, JobCategoryEnum.ADAPTACAO]:
                        category_gauges["Criação"].append(gauge_chart)
                    elif category in [JobCategoryEnum.STATIC_TRAFEGO_PAGO, JobCategoryEnum.ANIMATED_TRAFEGO_PAGO]:
                        category_gauges["Tráfego Pago"].append(gauge_chart)
                    elif category == JobCategoryEnum.CONTENT_PRODUCTION:
                        category_gauges["Produção de Conteúdo"].append(gauge_chart)
                    elif category not in [JobCategoryEnum.CARD_INSTAGRAM, JobCategoryEnum.REELS_INSTAGRAM, JobCategoryEnum.CAROUSEL_INSTAGRAM]:
                        category_gauges["Outras Redes"].append(gauge_chart)

            # Exibir gauges do Instagram
            if category_gauges["Instagram"]:
                st.subheader("Instagram")
                cols = st.columns(2)
                for i, gauge in enumerate(category_gauges["Instagram"]):
                    with cols[i % 2]:
                        st.plotly_chart(gauge)
                pie_chart = create_pie_chart(social_media_data, "Distribuição Instagram")
                st.plotly_chart(pie_chart)

            # Exibir gauges de outras categorias
            for key in ["Criação", "Tráfego Pago", "Produção de Conteúdo", "Outras Redes"]:
                if category_gauges[key]:
                    st.subheader(key)
                    cols = st.columns(3)
                    for i, gauge in enumerate(category_gauges[key]):
                        with cols[i % 3]:
                            st.plotly_chart(gauge)

        except KeyError as e:
            logging.error(f"Erro ao exibir os dados: {e}")
            st.error(f"Erro ao exibir os dados: {e}")

# Função auxiliar para criar um gráfico de pizza
def create_pie_chart(data, title):
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(title_text=title)
    return fig

# Certifique-se de que as funções `map_category_to_delivery_category` e `display_gauge_chart` estejam definidas


def get_last_month_date_range():
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)
    return first_day_of_last_month, last_day_of_last_month

def page_criacao():
    st.sidebar.header("Filtro de Cliente e Data")
    clientes_df = pd.read_sql_query("SELECT * FROM clients", engine)
    cliente_id = st.sidebar.selectbox("Selecione o Cliente", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0], key='unique_select_box_id_1')

    st.session_state["cliente_id"] = cliente_id

    first_day_of_last_month, last_day_of_last_month = get_last_month_date_range()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.sidebar.date_input("Data de início", value=first_day_of_last_month, key="data_inicio")
    with col2:
        data_fim = st.sidebar.date_input("Data de fim", value=last_day_of_last_month, key="data_fim")

    uploaded_file = st.sidebar.file_uploader("Upload de arquivo XLSX", type=["xlsx"], key="unique_file_uploader_key")
    if uploaded_file:
        logging.info("Arquivo XLSX enviado. Iniciando processamento...")
        try:
            process_xlsx_file(uploaded_file)
            st.success("Arquivo processado com sucesso e dados inseridos no banco de dados.")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
            logging.error(f"Erro ao processar o arquivo: {e}", exc_info=True)

    # Move a seleção das categorias de entrega para a barra lateral
    st.sidebar.header("Selecione as Categorias de Entrega")
    selected_delivery_categories = []
    for delivery_category in DeliveryCategoryEnum:
        if st.sidebar.checkbox(delivery_category.value, value=True):
            selected_delivery_categories.append(delivery_category)

    display_client_plan_status()

    delivery_data = get_delivery_control_data(cliente_id, data_inicio, data_fim)
    mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

    # Debug display data permanece na página principal
    debug_display_data(cliente_id, delivery_data, mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, selected_delivery_categories)

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
            JobCategoryEnum.FEED_INSTAGRAM: client.n_monthly_contracted_feed_instagram_mandalecas
        }

        mandalecas_usadas = {
            JobCategoryEnum.CRIACAO: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.CRIACAO),
            JobCategoryEnum.ADAPTACAO: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.ADAPTACAO),
            JobCategoryEnum.CONTENT_PRODUCTION: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.CONTENT_PRODUCTION),
            JobCategoryEnum.STORIES_INSTAGRAM: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.STORIES_INSTAGRAM),
            JobCategoryEnum.FEED_LINKEDIN: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.FEED_LINKEDIN),
            JobCategoryEnum.FEED_TIKTOK: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.FEED_TIKTOK),
            JobCategoryEnum.STORIES_REPOST_INSTAGRAM: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.STORIES_REPOST_INSTAGRAM),
            JobCategoryEnum.STATIC_TRAFEGO_PAGO: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.STATIC_TRAFEGO_PAGO),
            JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.ANIMATED_TRAFEGO_PAGO),
            JobCategoryEnum.FEED_INSTAGRAM: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.FEED_INSTAGRAM),
            JobCategoryEnum.CARD_INSTAGRAM: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.CARD_INSTAGRAM),
            JobCategoryEnum.CAROUSEL_INSTAGRAM: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.CAROUSEL_INSTAGRAM),
            JobCategoryEnum.REELS_INSTAGRAM: sum(job.used_mandalecas for job in client.delivery_controls if job.job_category == JobCategoryEnum.REELS_INSTAGRAM)
        }

        # Somando as mandalecas usadas de REELS_INSTAGRAM, CAROUSEL_INSTAGRAM e CARD_INSTAGRAM para FEED_INSTAGRAM
        mandalecas_usadas[JobCategoryEnum.FEED_INSTAGRAM] = (
            mandalecas_usadas[JobCategoryEnum.CARD_INSTAGRAM] +
            mandalecas_usadas[JobCategoryEnum.CAROUSEL_INSTAGRAM] +
            mandalecas_usadas[JobCategoryEnum.REELS_INSTAGRAM]
        )

        logging.info(f"Mandalecas usadas calculadas: {mandalecas_usadas}")

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
            JobCategoryEnum.FEED_INSTAGRAM: client.accumulated_feed_instagram_mandalecas
        }

        logging.info(f"Mandalecas acumuladas calculadas: {mandalecas_acumuladas}")

    return mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas
