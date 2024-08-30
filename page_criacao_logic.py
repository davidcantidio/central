import re
import streamlit as st
from utils import check_plan_status
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import (
    ContentProduction, 
    AttentionPoints, 
    RedesSociaisGuidance, 
    Client, 
    Users, 
    JobCategoryEnum, 
    DeliveryCategoryEnum, 
    RedesSociaisPlan, 
    RedesSociaisPlanStatusEnum
)
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
# Funções de Manipulação de Data de Envio
# ===========================================================

def salvar_data_envio(cliente_id, data_envio, model_class, status_function):
    logging.info(f"Salvando data de envio para cliente ID {cliente_id} com data {data_envio}")
    with Session(bind=engine) as session:
        try:
            if isinstance(data_envio, datetime):
                data_envio = data_envio.date()

            mes_inicio = data_envio.replace(day=1)
            logging.debug(f"Buscando registro existente para cliente ID {cliente_id} no mês {mes_inicio.strftime('%Y-%m')}")
            record = session.query(model_class).filter(
                model_class.client_id == cliente_id,
                func.strftime('%Y-%m', model_class.send_date) == mes_inicio.strftime('%Y-%m')
            ).first()

            client = session.query(Client).filter(Client.id == cliente_id).first()
            logging.debug(f"Cliente encontrado: {client}")

            # Obter o deadline_day do cliente
            if model_class == RedesSociaisPlan:
                deadline_day = client.monthly_plan_deadline_day
            elif model_class == RedesSociaisGuidance:
                deadline_day = client.monthly_redes_guidance_deadline_day
            else:
                raise ValueError("Classe de modelo desconhecida para determinação do deadline_day")

            if record:
                logging.debug(f"Registro encontrado, atualizando data de envio e status")
                record.send_date = data_envio
                record.updated_at = datetime.now()
                record.status = status_function(client, record, deadline_day)
            else:
                logging.debug(f"Nenhum registro existente encontrado, criando novo registro")
                record = model_class(
                    client_id=cliente_id,
                    send_date=data_envio,
                    updated_at=datetime.now(),
                    status=status_function(client, None, deadline_day),
                    plan_status=RedesSociaisPlanStatusEnum.AWAITING
                )
                session.add(record)

            logging.info(f"Commitando a transação no banco de dados")
            session.commit()
            st.success(f"Data de envio atualizada com sucesso.")
            st.session_state['send_date'] = data_envio

        except Exception as e:
            session.rollback()
            st.error(f"Erro ao atualizar a data de envio: {e}")
            logging.error(f"Erro ao atualizar a data de envio: {e}")

# ===========================================================
# Funções de Interface (UI)
# ===========================================================

def display_plan_or_guidance_modal(cliente_id, model_class, status_function, title_key, session_key):
    # Inicializa o modal fora dos containers estilizados
    modal = Modal(f"Data de Envio do {title_key}", key=f"enviar-{title_key.lower()}-modal", max_width=800)
    
    send_date = st.session_state.get(session_key)

    if send_date:
        open_modal = display_sent_info(send_date)
    else:
        open_modal = st.button(f"Enviar {title_key}", key=f"send_{title_key.lower()}_button")

    if open_modal:
        logging.info(f"Usuário clicou no botão 'Enviar {title_key}' para o cliente ID {cliente_id}")
        modal.open()

    # Verifica e abre o modal fora do container
    if modal.is_open():
        logging.info(f"Modal 'Data de Envio do {title_key}' foi aberto para o cliente ID {cliente_id}")
        with modal.container():
            selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            if st.button("Confirmar"):
                logging.info(f"Tentando salvar a data de envio para o cliente ID {cliente_id}")
                salvar_data_envio(cliente_id, selected_date, model_class, status_function)
                st.session_state[session_key] = selected_date
                modal.close()  # Fecha o modal
                st.success(f"Data de envio do {title_key.lower()} atualizada com sucesso!")
                st.rerun()  # Recarrega a página para refletir as mudanças

def create_modal(cliente_id, model_class, status_function, title_key, session_key):
    modal = Modal(f"Data de Envio do {title_key}", key=f"enviar-{title_key.lower()}-modal", max_width=800)

    if modal.is_open():
        with modal.container():
            selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            if st.button("Confirmar"):
                salvar_data_envio(cliente_id, selected_date, model_class, status_function)
                st.session_state[session_key] = selected_date
                modal.close()
                st.rerun()

    return modal

def display_sent_info(send_date):
    col1, col2 = st.columns([0.1, 0.3])

    with col1:
        st.write(f"Enviado em {send_date.strftime('%d/%m/%Y')}")

    with col2:
        return st.button("Editar", key="edit_button")

# ===========================================================
# Funções de Lógica de Negócios
# ===========================================================

def determinar_status(cliente, record, deadline_day):
    hoje = datetime.today().date()
    prazo = datetime(hoje.year, hoje.month, deadline_day).date()
    
    if record is None or record.send_date is None:
        if hoje > prazo:
            return RedesSociaisPlanStatusEnum.DELAYED
        else:
            return RedesSociaisPlanStatusEnum.AWAITING
    else:
        send_date = record.send_date
        if isinstance(send_date, datetime):
            send_date = send_date.date()
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

def create_timeline_chart(today, deadline_date, event_date, event_name="Enviado"):
    days_in_month = [date for date in pd.date_range(start=today.replace(day=1), end=today.replace(day=28) + pd.offsets.MonthEnd(1))]
    x_values = [day.strftime('%Y-%m-%d') for day in days_in_month]

    event_dates = [deadline_date.strftime('%Y-%m-%d')]
    event_colors = ["red"]
    event_texts = ["Deadline"]

    if event_date:
        event_dates.append(event_date.strftime('%Y-%m-%d'))
        event_colors.append("green")
        event_texts.append(event_name)

    fig = go.Figure()

    # Adicionando a linha do tempo com os dias do mês
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[1] * len(x_values),
        mode='lines+markers',
        line=dict(color='lightgrey', width=2),
        marker=dict(color='lightgrey', size=6),
        hoverinfo='x',
        showlegend=False
    ))

    # Adicionando os eventos com as legendas
    for date, color, text in zip(event_dates, event_colors, event_texts):
        text_position = "top center" if text == event_name else "bottom center"
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

def render_timeline_chart(today, deadline_date, event_date, event_name="Enviado"):
    fig = create_timeline_chart(today, deadline_date, event_date, event_name)
    st.plotly_chart(fig, use_container_width=True)

def display_gauge_chart(title, contracted, used, accumulated=0):
    if accumulated < 0:
        max_value = contracted  # Mantém o max_value como o contratado quando há um déficit
        deficit_start = contracted + accumulated  # Início do déficit (valor menor que o contratado)
        steps = [
            {'range': [0, deficit_start], 'color': "lightgray"},  # Intervalo até o início do déficit
            {'range': [deficit_start, contracted], 'color': "red"}  # Intervalo do déficit
        ]
    else:
        max_value = contracted + accumulated
        steps = [
            {'range': [0, contracted], 'color': "lightgray"},
            {'range': [contracted, max_value], 'color': "orange"}
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=used,
        title={'text': title, 'font': {'size': 20}},
        number={'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "green"},
            'steps': steps,
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': contracted
            }
        }
    ))

    fig.update_layout(
        autosize=False,
        width=350,
        height=300,
        margin=dict(l=20, r=20, t=50, b=100),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[
            dict(
                x=0.15, y=-0.05, xref='paper', yref='paper',
                text=f"Contratado: {contracted}",
                showarrow=False,
                font=dict(color="white", size=16),
                xanchor='center',
                yanchor='top',
                bgcolor='green',
                borderpad = 5,
                borderwidth=2,
                bordercolor='rgba(0,0,0,0)',  # Borda transparente
                opacity=1  # Ajusta a opacidade para um efeito mais suave
            ),
            dict(
                x=0.8, y=-0.05, xref='paper', yref='paper',
                text=f"<b>Acumulado:</b> {accumulated}",
                showarrow=False,
                font=dict(color="white", size=16),
                xanchor='center',
                yanchor='top',
                bgcolor='orange',
                borderpad = 5,
                borderwidth=2,
                bordercolor='rgba(0,0,0,0)',  # Borda transparente
                opacity=1  # Ajusta a opacidade para um efeito mais suave
            )
        ]
    )

    return fig

def create_pie_chart(data, title):
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(title_text=title)
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
    cliente_id = st.session_state.get("cliente_id")
    
    # Inicializa o modal fora dos containers estilizados
    modal = Modal("Data de Envio do Plano", key="enviar-plano-modal", max_width=800)

    with stylable_container(key="plan_status", 
                            css_styles="""
                            {
                                padding-bottom: 45px;                               
                            }
                            """,):
        with Session(bind=engine) as session:
            client = session.query(Client).filter(Client.id == cliente_id).first()
            redes_sociais_plan = session.query(RedesSociaisPlan).filter(RedesSociaisPlan.client_id == cliente_id).first()

            if redes_sociais_plan:
                plan_status = determinar_status(client, redes_sociais_plan, client.monthly_plan_deadline_day)
                if 'plan_sent_date' not in st.session_state or not st.session_state['plan_sent_date']:
                    st.session_state['plan_sent_date'] = redes_sociais_plan.send_date
            else:
                plan_status = "Plano não encontrado"
                st.session_state['plan_sent_date'] = None

            next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B')
            title = f"Planejamento Redes Sociais: {next_month.capitalize()}"

            # Exibir o título fora do container com borda
            display_client_header(client, title)

            today = datetime.today()
            deadline_date = datetime(today.year, today.month, client.monthly_plan_deadline_day)

            # Agora entra no container com borda
            with stylable_container(key="plan_timeline", 
                                    css_styles="""
                                    {
                                        border: 1px  solid #d3d3d3;
                                        border-radius: 10px;
                                        padding: 15px;
                                    
                                    }
                                    """,):

                render_timeline_chart(today, deadline_date, st.session_state['plan_sent_date'])

        if st.button("Enviar Plano"):
            logging.info(f"Usuário clicou no botão 'Enviar Plano' para o cliente ID {cliente_id}")
            modal.open()

    # Verifica e abre o modal fora do container
    if modal.is_open():
        logging.info(f"Modal 'Data de Envio do Plano' foi aberto para o cliente ID {cliente_id}")
        with modal.container():
            selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            if st.button("Confirmar"):
                logging.info(f"Tentando salvar a data de envio para o cliente ID {cliente_id}")
                salvar_data_envio(cliente_id, selected_date, RedesSociaisPlan, determinar_status)
                st.session_state['plan_sent_date'] = selected_date
                modal.close()  # Fecha o modal
                st.success("Data de envio do plano atualizada com sucesso!")
                st.rerun()  # Recarrega a página para refletir as mudanças


def display_redes_guidance_status():
    cliente_id = st.session_state.get("cliente_id")
    
    # Inicializa o modal fora dos containers estilizados
    modal = Modal("Data de Envio do Direcionamento", key="enviar-direcionamento-modal", max_width=800)

    with stylable_container(key="redes_guidance_status", 
                            css_styles="""
                            {
                                padding-bottom: 45px;
                            }
                            """):
        with Session(bind=engine) as session:
            client = session.query(Client).filter(Client.id == cliente_id).first()
            redes_sociais_guidance = session.query(RedesSociaisGuidance).filter(RedesSociaisGuidance.client_id == cliente_id).first()

            if redes_sociais_guidance:
                guidance_status = determinar_status(client, redes_sociais_guidance, client.monthly_redes_guidance_deadline_day)
                if 'guidance_send_date' not in st.session_state or not st.session_state['guidance_send_date']:
                    st.session_state['guidance_send_date'] = redes_sociais_guidance.send_date
            else:
                guidance_status = "Direcionamento não encontrado"
                st.session_state['guidance_send_date'] = None

            next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B')
            title = f"Direcionamento Redes Sociais: {next_month.capitalize()}"

            # Exibir o título fora do container com borda
            display_client_header(client, title)

            today = datetime.today()
            deadline_date = datetime(today.year, today.month, client.monthly_redes_guidance_deadline_day)

            # Agora entra no container com borda
            with stylable_container(key="guidance_timeline", 
                                    css_styles="""
                                    {
                                        border: 1px solid #d3d3d3;
                                        border-radius: 10px;
                                        padding: 15px;
                                    }
                                    """):
                render_timeline_chart(today, deadline_date, st.session_state['guidance_send_date'])

        if st.button("Enviar Direcionamento"):
            logging.info(f"Usuário clicou no botão 'Enviar Direcionamento' para o cliente ID {cliente_id}")
            modal.open()

    # Verifica e abre o modal fora do container
    if modal.is_open():
        logging.info(f"Modal 'Data de Envio do Direcionamento' foi aberto para o cliente ID {cliente_id}")
        with modal.container():
            selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            if st.button("Confirmar"):
                logging.info(f"Tentando salvar a data de envio para o cliente ID {cliente_id}")
                salvar_data_envio(cliente_id, selected_date, RedesSociaisGuidance, determinar_status)
                st.session_state['guidance_send_date'] = selected_date
                modal.close()  # Fecha o modal após salvar a data de envio
                st.rerun()

def display_client_header(client, title):
    st.write(f"**{title}**")


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
        logging.info(f"Dados obtidos: {df.shape[0]} registros encontrados")
    return df


def display_creation_and_adaptation_gauges(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.write("**Criação e Adaptação de Formato**")

    # Criar um único container para ambos os gráficos
    with stylable_container(key="creation_and_adaptation_gauge", 
                            css_styles="""
                            {
                                border: 1px solid #fff;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 45px;
                                max-width: 800px;
                            }
                            """):
        
        # Criar colunas internas para os dois gráficos
        col1, col2 = st.columns(2)

        with col1:
            gauge_chart = display_gauge_chart(
                title="Criação",
                contracted=mandalecas_contratadas.get(JobCategoryEnum.CRIACAO, 0),
                used=mandalecas_usadas.get(JobCategoryEnum.CRIACAO, 0),
                accumulated=mandalecas_acumuladas.get(JobCategoryEnum.CRIACAO, 0)
            )
            st.plotly_chart(gauge_chart, use_container_width=True)

        with col2:
            gauge_chart = display_gauge_chart(
                title="Adaptação de Formato",
                contracted=mandalecas_contratadas.get(JobCategoryEnum.ADAPTACAO, 0),
                used=mandalecas_usadas.get(JobCategoryEnum.ADAPTACAO, 0),
                accumulated=mandalecas_acumuladas.get(JobCategoryEnum.ADAPTACAO, 0)
            )
            st.plotly_chart(gauge_chart, use_container_width=True)

def display_paid_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.write("**Tráfego Pago**")
    with st.container(border=1):
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
    st.write("**Instagram**")
    with stylable_container(key="instagram_gauge", 
                            css_styles="""
                            {
                                border: 1px solid #d3d3d3;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 45px;
                            }
                            """):
        gauge_chart = display_gauge_chart(
            title="Instagram",
            contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_INSTAGRAM, 0),
            used=mandalecas_usadas.get(JobCategoryEnum.FEED_INSTAGRAM, 0),
            accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_INSTAGRAM, 0)
        )

        st.plotly_chart(gauge_chart)

        social_media_data = {
            "Carrossel Instagram": mandalecas_usadas.get(JobCategoryEnum.CAROUSEL_INSTAGRAM, 0),
            "Reels Instagram": mandalecas_usadas.get(JobCategoryEnum.REELS_INSTAGRAM, 0),
            "Card Instagram": mandalecas_usadas.get(JobCategoryEnum.CARD_INSTAGRAM, 0)
        }

        pie_chart = create_pie_chart(social_media_data, "Distribuição Instagram")
        st.plotly_chart(pie_chart)

def display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.write("**Outras Redes**")
    with stylable_container(key="other_networks_gauge", 
                            css_styles="""
                            {
                                border: 1px solid #d3d3d3;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 45px;
                            }
                            """):
        linkedin_gauge = display_gauge_chart(
            title="Feed LinkedIn",
            contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_LINKEDIN, 0),
            used=mandalecas_usadas.get(JobCategoryEnum.FEED_LINKEDIN, 0),
            accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_LINKEDIN, 0)
        )
        st.plotly_chart(linkedin_gauge)

        tiktok_gauge = display_gauge_chart(
            title="Feed TikTok",
            contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_TIKTOK, 0),
            used=mandalecas_usadas.get(JobCategoryEnum.FEED_TIKTOK, 0),
            accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_TIKTOK, 0)
        )
        st.plotly_chart(tiktok_gauge)

def display_content_production_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, cliente_id):
    st.write("**Produção de Conteúdo**")
    
    # Mantém o modal fora dos containers estilizados
    modal = Modal("Adicionar Nova Reunião", key="adicionar-reuniao-modal", max_width=800)
    
    with stylable_container(key="content_production_gauge", 
                            css_styles="""
                            {
                                border: 1px solid #d3d3d3;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 45px;
                            }
                            """):
        gauge_chart = display_gauge_chart(
            title="Produção de Conteúdo",
            contracted=mandalecas_contratadas.get(JobCategoryEnum.CONTENT_PRODUCTION, 0),
            used=mandalecas_usadas.get(JobCategoryEnum.CONTENT_PRODUCTION, 0),
            accumulated=mandalecas_acumuladas.get(JobCategoryEnum.CONTENT_PRODUCTION, 0)
        )
        st.plotly_chart(gauge_chart)

        # Exibir a tabela de produção de conteúdo dentro do mesmo container do gauge
        st.write("**Histórico de Reuniões de Produção de Conteúdo**")
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

    # Botão para adicionar nova reunião de produção de conteúdo fora do container
    if st.button("Adicionar Nova Reunião de Produção de Conteúdo"):
        logging.info(f"Usuário clicou no botão 'Adicionar Nova Reunião de Produção de Conteúdo' para o cliente ID {cliente_id}")
        modal.open()

    # Verifica e abre o modal fora do container
    if modal.is_open():
        logging.info(f"Modal 'Adicionar Nova Reunião' foi aberto para o cliente ID {cliente_id}")
        with modal.container():
            meeting_date = st.date_input("Data da Reunião", value=datetime.today())
            meeting_subject = st.text_input("Assunto")
            notes = st.text_area("Notas")

            if st.button("Salvar"):
                logging.info(f"Tentando salvar uma nova reunião de produção de conteúdo para o cliente ID {cliente_id}")
                save_new_content_production(cliente_id, meeting_date, meeting_subject, notes)
                logging.info(f"Nova reunião de produção de conteúdo salva com sucesso para o cliente ID {cliente_id}")
                st.rerun()
def display_content_production_table(cliente_id):
    # Mantém o modal fora dos containers estilizados
    modal = Modal("Adicionar Nova Reunião", key="adicionar-reuniao-modal", max_width=800)

    with stylable_container(key="content_production", 
                            css_styles="""
                            {
                                padding-bottom: 45px;
                            }
                            """):
        st.write("**Histórico de Reuniões de Produção de Conteúdo**")
        with stylable_container(key="content_production_table", 
                                css_styles="""
                                {
                                    border: 1px solid #d3d3d3;
                                    border-radius: 10px;
                                    padding: 15px;
                                }
                                """):
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

        if st.button("Adicionar Nova Reunião de Produção de Conteúdo"):
            logging.info(f"Usuário clicou no botão 'Adicionar Nova Reunião de Produção de Conteúdo' para o cliente ID {cliente_id}")
            modal.open()

    # Verifica e abre o modal fora do container
    if modal.is_open():
        logging.info(f"Modal 'Adicionar Nova Reunião' foi aberto para o cliente ID {cliente_id}")
        with modal.container():
            meeting_date = st.date_input("Data da Reunião", value=datetime.today())
            meeting_subject = st.text_input("Assunto")
            notes = st.text_area("Notas")

            if st.button("Salvar"):
                logging.info(f"Tentando salvar uma nova reunião de produção de conteúdo para o cliente ID {cliente_id}")
                save_new_content_production(cliente_id, meeting_date, meeting_subject, notes)
                logging.info(f"Nova reunião de produção de conteúdo salva com sucesso para o cliente ID {cliente_id}")
                st.rerun()
           
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

def display_attention_points_table(cliente_id):
    # Mantém o modal fora dos containers estilizados
    modal = Modal("Adicionar Novo Ponto de Atenção", key="adicionar-ponto-atencao-modal", max_width=800)

    with stylable_container(key="attention_points", 
                                css_styles="""
                                {
                                    padding-bottom: 45px;                               
                                }
                                """,):
        st.write("**Pontos de Atenção**")
        with stylable_container(key="plan_timeline", 
                                css_styles="""
                                {
                                    border: 1px  solid #d3d3d3;
                                    border-radius: 10px;
                                    padding: 15px;
                                
                                }
                                """,):
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

        if st.button("Adicionar Novo Ponto de Atenção"):
            logging.info(f"Usuário clicou no botão 'Adicionar Novo Ponto de Atenção' para o cliente ID {cliente_id}")
            modal.open()

    # Verifica e abre o modal fora do container
    if modal.is_open():
        logging.info(f"Modal 'Adicionar Novo Ponto de Atenção' foi aberto para o cliente ID {cliente_id}")
        with modal.container():
            attention_date = st.date_input("Data do Ponto de Atenção", value=datetime.today())
            attention_point = st.text_area("Ponto de Atenção")

            if st.button("Salvar"):
                logging.info(f"Tentando salvar um novo ponto de atenção para o cliente ID {cliente_id}")
                save_new_attention_point(cliente_id, attention_date, attention_point)
                logging.info(f"Novo ponto de atenção salvo com sucesso para o cliente ID {cliente_id}")
                st.rerun()

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


# Ajuste na função principal para passar o cliente_id corretamente
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

    # Criar colunas lado a lado para status do plano e direcionamento de redes sociais
    col1, col2 = st.columns(2)

    with col1:
        with stylable_container(key="plan_status_container", 
                                css_styles="""
                                {
                                    border: 1px solid #d3d3d3;
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin-bottom: 15px;
                                }
                                """):
            # Exibir status do plano
            display_client_plan_status()

    with col2:
        with stylable_container(key="guidance_status_container", 
                                css_styles="""
                                {
                                    border: 1px solid #d3d3d3;
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin-bottom: 15px;
                                }
                                """):
            # Exibir status do direcionamento
            display_redes_guidance_status()

    delivery_data = get_delivery_control_data(cliente_id, data_inicio, data_fim)
    mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)
    
    # Criar colunas lado a lado para criação e adaptação de formato
    col1, col2 = st.columns(2)

    with col1:
        with stylable_container(key="creation_and_adaptation_gauge_container", 
                                css_styles="""
                                {
                                    border: 1px solid #d3d3d3;
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin-bottom: 15px;
                                }
                                """):
            # Exibir gauges de criação e adaptação de formato
            display_creation_and_adaptation_gauges(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir outros gauges normalmente
    display_paid_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_instagram_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_content_production_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, cliente_id)
    display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
