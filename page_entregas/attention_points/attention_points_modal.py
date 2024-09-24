import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from common.models import AttentionPoints
import logging

def modal_attention_point_open(engine, modal):
    """
    Exibe o conteúdo do modal para adicionar um novo ponto de atenção.
    """
    cliente_id = st.session_state.get("cliente_id")
    logging.debug(f"modal_attention_point_open() chamado para o cliente ID {cliente_id}")

    with modal.container():
        with st.form(key='attention_point_form'):
            selected_date = st.date_input("Selecione a Data do Ponto de Atenção", value=datetime.today())
            attention_description = st.text_area("Descrição do Ponto de Atenção")
            submit_button = st.form_submit_button(label='Salvar')

            if submit_button:
                if attention_description:  # Verifica se a descrição não está vazia
                    save_new_attention_point(cliente_id, selected_date, attention_description, engine)
                    logging.info(f"Salvando novo ponto de atenção para o cliente ID {cliente_id} com data {selected_date}")

                    st.success("Ponto de atenção adicionado com sucesso!")
                    # Fecha o modal
                    modal.close()
                    # Recarrega a página para atualizar a tabela
                    st.experimental_rerun()
                else:
                    st.error("A descrição do ponto de atenção não pode estar vazia.")

def save_new_attention_point(cliente_id, attention_date, attention_point, engine):
    """
    Salva um novo ponto de atenção no banco de dados.
    """
    try:
        with Session(bind=engine) as session:
            new_entry = AttentionPoints(
                client_id=cliente_id,
                date=attention_date,
                attention_point=attention_point
            )
            session.add(new_entry)
            session.commit()
            logging.info(f"Novo ponto de atenção salvo no banco de dados para o cliente ID {cliente_id}.")
    except Exception as e:
        logging.error(f"Erro ao salvar o ponto de atenção: {e}")
        st.error(f"Erro ao salvar o ponto de atenção: {e}")
