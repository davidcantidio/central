import streamlit as st
import sqlite3
import pandas as pd

# Função para obter clientes do banco de dados
def get_clientes():
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        df = pd.read_sql_query("SELECT * FROM clients", conn)
    return df

# Página inicial que exibe cartões de clientes
def home():
    st.title("Clientes")
    df = get_clientes()
    filtro_nome = st.text_input("Filtrar por nome")
    if filtro_nome:
        df = df[df["name"].str.contains(filtro_nome, case=False, na=False)]
    
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    for i, cliente in df.iterrows():
        with cols[i % 3]:
            with st.container():
                st.write(f"**{cliente['name']}**")
                st.write(f"Tipo de Negócio: {cliente['business_type']}")
                st.write(f"Telefone: {cliente['phone']}")
                st.write(f"Email: {cliente['email']}")
                if st.button("Ver detalhes", key=cliente["id"]):
                    st.session_state["cliente_id"] = cliente["id"]
                    st.rerun()
