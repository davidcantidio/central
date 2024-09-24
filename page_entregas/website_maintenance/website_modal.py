# import streamlit as st
# from datetime import datetime
# from streamlit_modal import Modal
# from sqlalchemy.orm import Session
# from common.models import WebsiteMaintenance
# from common.database import engine
# import logging

# def modal_website_maintenance_open():
#     cliente_id = st.session_state.get("cliente_id")

#     # Inicializa o modal para adicionar manutenção de website
#     modal = Modal("Adicionar Data de Manutenção de Website", key="adicionar-manutencao-modal", max_width=800)

#     if modal.is_open():
#         with modal.container():
#             selected_date = st.date_input("Selecione a Data de Manutenção", value=datetime.today())
#             if st.button("Salvar"):
#                 save_website_maintenance_date(cliente_id, selected_date)
#                 modal.close()
#                 st.success("Data de manutenção adicionada com sucesso!")
#                 st.rerun()

# def save_website_maintenance_date(cliente_id, selected_date):
#     try:
#         with Session(bind=engine) as session:
#             new_entry = WebsiteMaintenance(
#                 client_id=cliente_id,
#                 date=selected_date
#             )
#             session.add(new_entry)
#             session.commit()
#             logging.info(f"Data de manutenção para o cliente ID {cliente_id} adicionada com sucesso.")
#     except Exception as e:
#         st.error(f"Erro ao salvar a data de manutenção: {e}")
#         logging.error(f"Erro ao salvar a data de manutenção: {e}")
