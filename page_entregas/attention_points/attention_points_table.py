import streamlit as st
import pandas as pd
import logging


# ===========================================================
# Funções para Exibição da Tabela de Pontos de Atenção
# ===========================================================

def display_attention_points_table(cliente_id, data_inicio, data_fim, engine):
    """
    Exibe a tabela de pontos de atenção para um cliente específico, em um intervalo de datas.
    """
    try:
        # Query para buscar pontos de atenção no banco de dados
        with engine.connect() as conn:
            query = f"""
                SELECT * FROM pontos_de_atencao 
                WHERE client_id = {cliente_id} 
                AND date BETWEEN '{data_inicio}' AND '{data_fim}'
            """
            attention_points_df = pd.read_sql_query(query, conn)

        if attention_points_df.empty:
            st.info("Nenhum ponto de atenção encontrado para o período selecionado.")
        else:
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

