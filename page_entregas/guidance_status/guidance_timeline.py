# import streamlit as st
# from datetime import datetime, timedelta
# from common.models import Client, RedesSociaisGuidance
# from page_entregas.utils.assessoria_plan_utils import determinar_status
# from page_entregas.utils.timeline import render_timeline_chart
# from sqlalchemy.orm import Session
# from common.database import engine

# # Função para exibir a linha do tempo do direcionamento
# def display_guidance_timeline(cliente_id):
#     # Abrindo uma sessão com o banco de dados
#     with Session(bind=engine) as session:
#         # Consultando o cliente e o status do direcionamento
#         client = session.query(Client).filter(Client.id == cliente_id).first()
#         redes_sociais_guidance = session.query(RedesSociaisGuidance).filter(RedesSociaisGuidance.client_id == cliente_id).first()

#         # Verificando se o direcionamento existe
#         if redes_sociais_guidance:
#             # Determina o status do direcionamento e recupera a data de envio
#             guidance_status = determinar_status(client, redes_sociais_guidance, client.monthly_redes_guidance_deadline_day)
#             if 'guidance_send_date' not in st.session_state or not st.session_state['guidance_send_date']:
#                 st.session_state['guidance_send_date'] = redes_sociais_guidance.send_date
#         else:
#             guidance_status = "Direcionamento não encontrado"
#             st.session_state['guidance_send_date'] = None

#         # Exibir o título da linha do tempo
#         next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B')
#         title = f"Direcionamento Redes Sociais: {next_month.capitalize()}"
#         st.write(f"**{title}**")

#         # Definir datas importantes
#         today = datetime.today()
#         deadline_date = datetime(today.year, today.month, client.monthly_redes_guidance_deadline_day)

#         # Renderizar a linha do tempo
#         render_timeline_chart(today, deadline_date, st.session_state['guidance_send_date'])
