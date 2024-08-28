import re
import streamlit as st
from utils import check_plan_status
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import ContentProduction, AttentionPoints, RedesSociaisGuidance, Client, Users, JobCategoryEnum, DeliveryCategoryEnum, RedesSociaisPlan, RedesSociaisPlanStatusEnum
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
from streamlit_extras.stylable_container import stylable_container
from streamlit_modal import Modal
from datetime import datetime


# ===========================================================
# Configurações Iniciais e Utilidades
# ===========================================================

# Configurar localidade para português
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

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


# ===========================================================
# Funções de Manipulação de Data de Envio do Plano
# ===========================================================

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


# ===========================================================
# Funções de Interface (UI)
# ===========================================================

def display_client_header(client, title):
    st.subheader(client.name)  # Nome do cliente em uma linha separada
    st.write(f"**{title}**")   # Título em uma linha abaixo

def display_plan_sent_info(plan_sent_date):
    col1, col2 = st.columns([0.1, 0.3])  # Ajusta a largura das colunas para mantê-las na mesma linha

    with col1:
        st.write(f"Enviado em {plan_sent_date.strftime('%d/%m/%Y')}")

    with col2:
        return st.button("Editar", key="edit_plan_button")

def create_plan_modal(cliente_id):
    from streamlit_modal import Modal
    modal = Modal("Data de Envio do Plano", key="enviar-plano-modal", max_width=800)

    if modal.is_open():
        with modal.container():
            selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            if st.button("Confirmar"):
                salvar_data_envio_plano(cliente_id, selected_date)
                st.session_state['plan_sent_date'] = selected_date
                modal.close()
                st.experimental_rerun()

    return modal

def display_send_plan_modal(cliente_id):
    plan_sent_date = st.session_state.get('plan_sent_date')

    if plan_sent_date:
        open_modal = display_plan_sent_info(plan_sent_date)
    else:
        open_modal = st.button("Enviar Plano", key="send_plan_button")

    modal = create_plan_modal(cliente_id)

    if open_modal:
        modal.open()


# ===========================================================
# Funções de Lógica de Negócios
# ===========================================================

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


# ===========================================================
# Funções de Exibição de Gráficos
# ===========================================================

# Função para determinar o status do direcionamento de redes sociais
def determinar_status_guidance(cliente, guidance):
    hoje = datetime.today().date()
    prazo = datetime(hoje.year, hoje.month, cliente.monthly_redes_guidance_deadline_day).date()
    
    if guidance is None or guidance.send_date is None:
        if hoje > prazo:
            return RedesSociaisPlanStatusEnum.DELAYED
        else:
            return RedesSociaisPlanStatusEnum.AWAITING
    else:
        send_date = guidance.send_date
        if isinstance(send_date, datetime):
            send_date = send_date.date()
        if send_date <= prazo:
            return RedesSociaisPlanStatusEnum.ON_TIME
        else:
            return RedesSociaisPlanStatusEnum.DELAYED

# Função para exibir a data de envio do direcionamento já enviado
def display_guidance_sent_info(send_date):
    col1, col2 = st.columns([0.1, 0.3])

    with col1:
        st.write(f"Enviado em {send_date.strftime('%d/%m/%Y')}")

    with col2:
        return st.button("Editar", key="edit_guidance_button")

# Função para salvar a data de envio do direcionamento
def salvar_data_envio_guidance(cliente_id, send_date):
    with Session(bind=engine) as session:
        try:
            if isinstance(send_date, datetime):
                send_date = send_date.date()

            send_month_start = send_date.replace(day=1)
            redes_sociais_guidance = session.query(RedesSociaisGuidance).filter(
                RedesSociaisGuidance.client_id == cliente_id,
                func.strftime('%Y-%m', RedesSociaisGuidance.send_date) == send_month_start.strftime('%Y-%m')
            ).first()

            client = session.query(Client).filter(Client.id == cliente_id).first()

            if redes_sociais_guidance:
                redes_sociais_guidance.send_date = send_date
                redes_sociais_guidance.updated_at = datetime.now()
                redes_sociais_guidance.status = determinar_status_guidance(client, redes_sociais_guidance)
            else:
                redes_sociais_guidance = RedesSociaisGuidance(
                    client_id=cliente_id,
                    send_date=send_date,
                    updated_at=datetime.now(),
                    status=determinar_status_guidance(client, None),
                    plan_status=RedesSociaisPlanStatusEnum.AWAITING
                )
                session.add(redes_sociais_guidance)

            session.commit()
            st.success("Data de envio do direcionamento atualizada com sucesso.")
            st.session_state['guidance_send_date'] = send_date

        except Exception as e:
            session.rollback()
            st.error(f"Erro ao atualizar a data de envio do direcionamento: {e}")
            logging.error(f"Erro ao atualizar a data de envio do direcionamento: {e}")

def create_redes_plan_timeline_chart(today, deadline_date, plan_sent_date):
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

def render_redes_plan_timeline_chart(today, deadline_date, plan_sent_date):
    fig = create_redes_plan_timeline_chart(today, deadline_date, plan_sent_date)
    st.plotly_chart(fig, use_container_width=True)

# Função para renderizar o gráfico de linha do tempo do direcionamento de redes sociais
def render_redes_guidance_timeline_chart(today, deadline_date, send_date):
    fig = create_redes_guidance_timeline_chart(today, deadline_date, send_date)
    st.plotly_chart(fig, use_container_width=True)

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

def display_redes_guidance_status():
    cliente_id = st.session_state.get("cliente_id")
    with Session(bind=engine) as session:
        client = session.query(Client).filter(Client.id == cliente_id).first()
        redes_sociais_guidance = session.query(RedesSociaisGuidance).filter(RedesSociaisGuidance.client_id == cliente_id).first()

        if redes_sociais_guidance:
            guidance_status = determinar_status_guidance(client, redes_sociais_guidance)
            if 'guidance_send_date' not in st.session_state or not st.session_state['guidance_send_date']:
                st.session_state['guidance_send_date'] = redes_sociais_guidance.send_date
        else:
            guidance_status = "Direcionamento não encontrado"
            st.session_state['guidance_send_date'] = None

        next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B')
        title = f"Direcionamento Redes Sociais: {next_month.capitalize()}"

        today = datetime.today()
        deadline_date = datetime(today.year, today.month, client.monthly_redes_guidance_deadline_day)

        # Exibir título e informações do cliente
        display_client_header(client, title)

        # Exibir botão de envio/edição do direcionamento e modal
        send_guidance_modal(cliente_id)

        # Renderizar gráfico de linha do tempo
        render_redes_guidance_timeline_chart(today, deadline_date, st.session_state['guidance_send_date'])

# Função para criar o modal de envio do direcionamento
def send_guidance_modal(cliente_id):
    modal = Modal("Data de Envio do Direcionamento", key="enviar-guidance-modal", max_width=800)

    guidance_send_date = st.session_state.get('guidance_send_date')

    if guidance_send_date:
        open_modal = display_guidance_sent_info(guidance_send_date)
    else:
        open_modal = st.button("Enviar Direcionamento", key="send_guidance_button")

    if open_modal:
        modal.open()

    if modal.is_open():
        with modal.container():
            selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            if st.button("Confirmar"):
                salvar_data_envio_guidance(cliente_id, selected_date)
                st.session_state['guidance_send_date'] = selected_date
                modal.close()
                st.experimental_rerun()

def create_pie_chart(data, title):
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(title_text=title)
    return fig

def create_redes_guidance_timeline_chart(today, deadline_date, send_date):
    days_in_month = [date for date in pd.date_range(start=today.replace(day=1), end=today.replace(day=28) + pd.offsets.MonthEnd(1))]
    x_values = [day.strftime('%Y-%m-%d') for day in days_in_month]

    event_dates = [deadline_date.strftime('%Y-%m-%d')]
    event_colors = ["red"]
    event_texts = ["Deadline"]

    if send_date:
        event_dates.append(send_date.strftime('%Y-%m-%d'))
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
# ===========================================================
# Funções Principais da Página
# ===========================================================


def get_last_month_date_range():
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)
    return first_day_of_last_month, last_day_of_last_month


def display_client_plan_status():
    with st.container(border=1):
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

            # Exibir botão de envio/edição do plano e modal
            display_send_plan_modal(cliente_id)

            # Renderizar gráfico de linha do tempo
            render_redes_plan_timeline_chart(today, deadline_date, st.session_state['plan_sent_date'])


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


def display_creation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.subheader("Criação")

    gauge_chart = display_gauge_chart(
        title="Criação",
        contracted=mandalecas_contratadas.get(JobCategoryEnum.CRIACAO, 0),
        used=mandalecas_usadas.get(JobCategoryEnum.CRIACAO, 0),
        accumulated=mandalecas_acumuladas.get(JobCategoryEnum.CRIACAO, 0)
    )

    st.plotly_chart(gauge_chart)


def display_paid_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.subheader("Tráfego Pago")

    gauge_chart = display_gauge_chart(
        title="Tráfego Pago",
        contracted=mandalecas_contratadas.get(JobCategoryEnum.STATIC_TRAFEGO_PAGO, 0) +
                    mandalecas_contratadas.get(JobCategoryEnum.ANIMATED_TRAFEGO_PAGO, 0),
        used=mandalecas_usadas.get(JobCategoryEnum.STATIC_TRAFEGO_PAGO, 0) +
              mandalecas_usadas.get(JobCategoryEnum.ANIMATED_TRAFEGO_PAGO, 0),
        accumulated=mandalecas_acumuladas.get(JobCategoryEnum.STATIC_TRAFEGO_PAGO, 0) +
                    mandalecas_acumuladas.get(JobCategoryEnum.ANIMATED_TRAFEGO_PAGO, 0)
    )

    st.plotly_chart(gauge_chart)


def display_instagram_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.subheader("Instagram")

    gauge_chart = display_gauge_chart(
        title="Instagram",
        contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_INSTAGRAM, 0),
        used=mandalecas_usadas.get(JobCategoryEnum.FEED_INSTAGRAM, 0),
        accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_INSTAGRAM, 0)
    )

    st.plotly_chart(gauge_chart)

    # Dados para o gráfico de pizza
    social_media_data = {
        "Carrossel Instagram": mandalecas_usadas.get(JobCategoryEnum.CAROUSEL_INSTAGRAM, 0),
        "Reels Instagram": mandalecas_usadas.get(JobCategoryEnum.REELS_INSTAGRAM, 0),
        "Card Instagram": mandalecas_usadas.get(JobCategoryEnum.CARD_INSTAGRAM, 0)
    }

    pie_chart = create_pie_chart(social_media_data, "Distribuição Instagram")
    st.plotly_chart(pie_chart)

def display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.subheader("Outras Redes")

    # Gauge para LinkedIn
    linkedin_gauge = display_gauge_chart(
        title="Feed LinkedIn",
        contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_LINKEDIN, 0),
        used=mandalecas_usadas.get(JobCategoryEnum.FEED_LINKEDIN, 0),
        accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_LINKEDIN, 0)
    )
    st.plotly_chart(linkedin_gauge)

    # Gauge para TikTok
    tiktok_gauge = display_gauge_chart(
        title="Feed TikTok",
        contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_TIKTOK, 0),
        used=mandalecas_usadas.get(JobCategoryEnum.FEED_TIKTOK, 0),
        accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_TIKTOK, 0)
    )
    st.plotly_chart(tiktok_gauge)

def display_content_production_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.subheader("Produção de Conteúdo")

    gauge_chart = display_gauge_chart(
        title="Produção de Conteúdo",
        contracted=mandalecas_contratadas.get(JobCategoryEnum.CONTENT_PRODUCTION, 0),
        used=mandalecas_usadas.get(JobCategoryEnum.CONTENT_PRODUCTION, 0),
        accumulated=mandalecas_acumuladas.get(JobCategoryEnum.CONTENT_PRODUCTION, 0)
    )

    st.plotly_chart(gauge_chart)

def display_content_production_table(cliente_id):
    st.subheader("Histórico de Reuniões de Produção de Conteúdo")

    with Session(bind=engine) as session:
        content_production_data = session.query(ContentProduction).filter(ContentProduction.client_id == cliente_id).all()

        if not content_production_data:
            content_production_df = pd.DataFrame(columns=['Data da Reunião', 'Assunto', 'Notas'])
        else:
            content_production_df = pd.DataFrame([{
                'Data da Reunião': row.meeting_date.strftime('%Y-%m-%d') if row.meeting_date else '',
                'Assunto': row.meeting_subject,
                'Notas': row.notes
            } for row in content_production_data])

        st.table(content_production_df)

    # Modal para adicionar nova reunião de produção de conteúdo
    modal = Modal("Adicionar Nova Reunião", key="adicionar-reuniao-modal", max_width=800)

    if st.button("Adicionar Nova Reunião de Produção de Conteúdo"):
        modal.open()

    if modal.is_open():
        with modal.container():
            meeting_date = st.date_input("Data da Reunião", value=datetime.today())
            meeting_subject = st.text_input("Assunto")
            notes = st.text_area("Notas")

            if st.button("Salvar"):
                save_new_content_production(cliente_id, meeting_date, meeting_subject, notes)
                st.experimental_rerun()
                
def save_new_content_production(cliente_id, meeting_date, meeting_subject, notes):
    with Session(bind=engine) as session:
        new_entry = ContentProduction(
            client_id=cliente_id,
            meeting_date=meeting_date,
            meeting_subject=meeting_subject,
            notes=notes
        )
        session.add(new_entry)
        session.commit()
        st.success("Reunião de Produção de Conteúdo adicionada com sucesso!")

def edit_content_production_entry(cliente_id, entry):
    st.subheader(f"Editar Reunião (ID: {entry.id})")

    # Datepicker para selecionar a data
    meeting_date = st.date_input("Data da Reunião", value=entry.meeting_date or datetime.today())

    # Campos de texto para editar os outros detalhes
    meeting_subject = st.text_input("Assunto", value=entry.meeting_subject or "")
    notes = st.text_area("Notas", value=entry.notes or "")

    if st.button("Salvar Alterações"):
        with Session(bind=engine) as session:
            entry.meeting_date = meeting_date
            entry.meeting_subject = meeting_subject
            entry.notes = notes

            session.commit()
            st.success("Alterações salvas com sucesso!")

def display_attention_points_table(cliente_id):

    st.subheader("Pontos de Atenção")

    with Session(bind=engine) as session:
        attention_points_data = session.query(AttentionPoints).filter(AttentionPoints.client_id == cliente_id).all()

        if not attention_points_data:
            attention_points_df = pd.DataFrame(columns=['Data', 'Ponto de Atenção'])
        else:
            attention_points_df = pd.DataFrame([{
                'Data': row.date.strftime('%Y-%m-%d') if row.date else '',
                'Ponto de Atenção': row.attention_point
            } for row in attention_points_data])

        st.table(attention_points_df)

    # Modal para adicionar novo ponto de atenção
    modal = Modal("Adicionar Novo Ponto de Atenção", key="adicionar-ponto-atencao-modal", max_width=800)

    if st.button("Adicionar Novo Ponto de Atenção"):
        modal.open()

    if modal.is_open():
        with modal.container():
            attention_date = st.date_input("Data do Ponto de Atenção", value=datetime.today())
            attention_point = st.text_area("Ponto de Atenção")

            if st.button("Salvar"):
                save_new_attention_point(cliente_id, attention_date, attention_point)
                st.experimental_rerun()


def save_new_attention_point(cliente_id, attention_date, attention_point):
    with Session(bind=engine) as session:
        new_entry = AttentionPoints(
            client_id=cliente_id,
            date=attention_date,
            attention_point=attention_point
        )
        session.add(new_entry)
        session.commit()
        st.success("Ponto de Atenção adicionado com sucesso!")

def page_criacao():
    st.sidebar.header("Filtro de Cliente e Data")
    clientes_df = pd.read_sql_query("SELECT * FROM clients", engine)
    cliente_id = st.sidebar.selectbox(
        "Selecione o Cliente", 
        clientes_df['id'], 
        format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0], 
        key='unique_select_box_id_1'
    )

    st.session_state["cliente_id"] = cliente_id

    first_day_of_last_month, last_day_of_last_month = get_last_month_date_range()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.sidebar.date_input("Data de início", value=first_day_of_last_month, key="data_inicio")
    with col2:
        data_fim = st.sidebar.date_input("Data de fim", value=last_day_of_last_month, key="data_fim")

    uploaded_file = st.sidebar.file_uploader("Upload de arquivo XLSX", type=["xlsx"], key="unique_file_uploader_key")
    if uploaded_file:
        process_xlsx_file(uploaded_file)

    # Exibir tabela interativa de pontos de atenção
    display_attention_points_table(cliente_id)

    # Exibir tabela interativa de produção de conteúdo
    display_content_production_table(cliente_id)

    # Exibir status do plano
    display_client_plan_status()

    # Exibir status do direcionamento de redes sociais
    display_redes_guidance_status()

    delivery_data = get_delivery_control_data(cliente_id, data_inicio, data_fim)
    mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

    # Exibir gráficos de gauge para cada categoria
    display_creation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_paid_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_instagram_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_content_production_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
