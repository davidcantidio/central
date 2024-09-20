import streamlit as st
from page_entregas.utils.assessoria_plan_utils import salvar_data_envio, determinar_status
from common.models import RedesSociaisPlan
from streamlit_modal import Modal
from datetime import datetime
import logging

# Função para exibir o modal de envio do plano
def display_plan_modal(cliente_id):
    # Inicializa o modal fora dos containers estilizados
    modal = Modal("Data de Envio do Plano", key="enviar-plano-modal", max_width=800)

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
