import logging
import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from common.models import ContentProduction
from common.database import engine
from streamlit_modal import Modal

# Função que abre o modal para adicionar uma nova reunião de Produção de Conteúdo
def modal_content_production_open(cliente_id):
    logging.debug(f"modal_content_production_open() chamado para o cliente ID {cliente_id}")

    # Inicializa o modal para a reunião de Produção de Conteúdo com uma chave única
    modal = Modal("Adicionar Nova Reunião de Produção de Conteúdo", key="adicionar-reuniao-content-modal", max_width=800)
    logging.debug("Modal criado com sucesso.")

    # Verifica se o modal está aberto e apresenta o formulário
    if modal.is_open():
        logging.info(f"Modal 'Adicionar Reunião de Produção de Conteúdo' está aberto para o cliente ID {cliente_id}.")
        with modal.container():
            # Campos de entrada para a nova reunião de Produção de Conteúdo
            meeting_date = st.date_input("Data da Reunião", value=datetime.today())
            meeting_subject = st.text_input("Assunto")
            notes = st.text_area("Notas")
            logging.debug("Campos de entrada exibidos.")

            # Botão para salvar a reunião de Produção de Conteúdo
            if st.button("Salvar"):
                logging.info("Botão 'Salvar' foi clicado.")
                if meeting_subject:  # Verifica se o campo assunto não está vazio
                    save_new_content_production(cliente_id, meeting_date, meeting_subject, notes)
                    modal.close()  # Fecha o modal após salvar
                    logging.info(f"Reunião de Produção de Conteúdo salva com sucesso para o cliente ID {cliente_id}.")
                    st.rerun()  # Recarrega a página para refletir as mudanças
                else:
                    st.error("O campo Assunto não pode estar vazio.")
                    logging.warning("Tentativa de salvar reunião de Produção de Conteúdo sem o assunto preenchido.")
    else:
        logging.debug("Modal 'Adicionar Reunião de Produção de Conteúdo' não foi aberto.")

# Função para salvar a nova reunião de Produção de Conteúdo no banco de dados
def save_new_content_production(cliente_id, meeting_date, meeting_subject, notes):
    try:
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
            logging.info(f"Nova reunião de Produção de Conteúdo salva no banco de dados para o cliente ID {cliente_id}.")
    except Exception as e:
        logging.error(f"Erro ao salvar a reunião de Produção de Conteúdo: {e}")
        st.error(f"Erro ao salvar a reunião de Produção de Conteúdo: {e}")
