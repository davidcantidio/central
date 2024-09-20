import streamlit as st
from common.models import Client, RedesSociaisPlan
from page_entregas.utils.assessoria_plan_utils import determinar_status
from page_entregas.utils.timeline import render_timeline_chart


from sqlalchemy.orm import Session
from datetime import datetime

# Função para exibir a linha do tempo do plano de redes sociais
def display_plan_timeline(cliente_id):
    with Session(bind=st.session_state["engine"]) as session:
        # Busca os dados do cliente e o plano de redes sociais
        client = session.query(Client).filter(Client.id == cliente_id).first()
        redes_sociais_plan = session.query(RedesSociaisPlan).filter(RedesSociaisPlan.client_id == cliente_id).first()

        # Determina o status do plano e a data de envio do plano
        if redes_sociais_plan:
            plan_status = determinar_status(client, redes_sociais_plan, client.monthly_plan_deadline_day)
            if 'plan_sent_date' not in st.session_state or not st.session_state['plan_sent_date']:
                st.session_state['plan_sent_date'] = redes_sociais_plan.send_date
        else:
            plan_status = "Plano não encontrado"
            st.session_state['plan_sent_date'] = None

        # Gera o título para a linha do tempo com base no próximo mês
        next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B')
        title = f"Planejamento Redes Sociais: {next_month.capitalize()}"

        # Exibe o título
        st.write(f"**{title}**")

        # Define a data de hoje e a data do deadline
        today = datetime.today()
        deadline_date = datetime(today.year, today.month, client.monthly_plan_deadline_day)

        # Renderiza a linha do tempo do plano
        render_timeline_chart(today, deadline_date, st.session_state['plan_sent_date'])
