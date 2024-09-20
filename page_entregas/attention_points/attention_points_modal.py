import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from common.models import AttentionPoints
from streamlit_modal import Modal
import logging

# ===========================================================
# Funções para Pontos de Atenção (Attention Points)
# ===========================================================

def display_attention_points_table(cliente_id, data_inicio, data_fim, engine):
    """
    Exibe a tabela de pontos de atenção para um cliente, em um intervalo de datas.
    """
    try:
        with engine.connect() as conn:
            query = f"""
                SELECT * FROM pontos_de_atencao 
                WHERE client_id = {cliente_id} 
                AND date BETWEEN '{data_inicio}' AND '{data_fim}'
            """
            attention_points_df = pd.read_sql_query(query, conn)
            st.table(attention_points_df)
            logging.info("Tabela de pontos de atenção exibida corretamente.")

        # Chamar o modal ao clicar no botão "Adicionar Ponto de Atenção"
        if st.button("Adicionar Ponto de Atenção"):
            logging.info(f"Usuário clicou no botão 'Adicionar Ponto de Atenção' para o cliente ID {cliente_id}")
            st.session_state["open_attention_modal"] = True
            logging.info(f"Flag 'open_attention_modal' setada para True")

    except Exception as e:
        st.error(f"Erro ao carregar pontos de atenção: {e}")
        logging.error(f"Erro ao carregar pontos de atenção: {e}")


def modal_attention_point_open(engine):
    """
    Abre o modal para adicionar um novo ponto de atenção.
    """
    cliente_id = st.session_state.get("cliente_id")
    logging.debug(f"modal_attention_point_open() chamado para o cliente ID {cliente_id}")

    # Inicializa o modal para pontos de atenção com uma chave única
    modal = Modal("Adicionar Ponto de Atenção", key="adicionar-ponto-modal", max_width=800)
    logging.debug("Modal criado com sucesso.")

    # Verifica se a flag no session state está habilitada e se o modal foi criado
    if st.session_state.get("open_attention_modal", False):
        logging.info(f"Abrindo o modal 'Adicionar Ponto de Atenção' para o cliente ID {cliente_id}")
        modal.open()

    # Verifica se o modal foi realmente aberto
    if modal.is_open():
        logging.info(f"Modal 'Adicionar Ponto de Atenção' está aberto para o cliente ID {cliente_id}.")
        with modal.container():
            # Campos de entrada para o novo ponto de atenção
            selected_date = st.date_input("Selecione a Data do Ponto de Atenção", value=datetime.today())
            attention_description = st.text_area("Descrição do Ponto de Atenção")
            logging.debug("Campos de entrada exibidos.")

            # Botão para salvar o ponto de atenção
            if st.button("Salvar"):
                logging.info("Botão 'Salvar' foi clicado.")
                if attention_description:  # Verifica se a descrição não está vazia
                    save_new_attention_point(cliente_id, selected_date, attention_description, engine)
                    logging.info(f"Salvando novo ponto de atenção para o cliente ID {cliente_id} com data {selected_date}")
                    st.session_state["open_attention_modal"] = False  # Fecha o modal após salvar
                    modal.close()  # Fecha o modal após salvar
                    logging.info(f"Ponto de atenção salvo e modal fechado para o cliente ID {cliente_id}.")
                    st.rerun()  # Recarrega a página para refletir as mudanças
                else:
                    st.error("A descrição do ponto de atenção não pode estar vazia.")
                    logging.warning("Tentativa de salvar ponto de atenção sem descrição.")
    else:
        logging.debug("Modal 'Adicionar Ponto de Atenção' não foi aberto.")


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
            st.success("Ponto de Atenção adicionado com sucesso!")
            logging.info(f"Novo ponto de atenção salvo no banco de dados para o cliente ID {cliente_id}.")
    except Exception as e:
        logging.error(f"Erro ao salvar o ponto de atenção: {e}")
        st.error(f"Erro ao salvar o ponto de atenção: {e}")

