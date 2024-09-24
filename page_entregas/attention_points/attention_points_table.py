import streamlit as st
import pandas as pd
import logging

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

        # O botão de "Adicionar Ponto de Atenção" foi removido daqui para evitar duplicação
        # O modal será aberto via `attention_points_modal.py`

    except Exception as e:
        st.error(f"Erro ao carregar pontos de atenção: {e}")
        logging.error(f"Erro ao carregar pontos de atenção: {e}")
