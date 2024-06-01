import streamlit as st
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu

# Função para obter clientes do banco de dados
def get_clientes():
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        df = pd.read_sql_query("SELECT * FROM clients", conn)
    return df

# Função para exibir os detalhes do cliente
def show_cliente(cliente_id):
    df = get_clientes()
    cliente = df[df["id"] == cliente_id].iloc[0]
    
    st.title(f"Cliente: {cliente['name']}")
    
    with st.sidebar:
        menu = option_menu(
            menu_title="Menu do Cliente",
            options=["Contrato"],
            icons=["file-earmark-text"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

    if menu == "Contrato":
        st.header("Informações do Contrato")
        st.write(f"Nome: {cliente['name']}")
        st.write(f"Mandaleças Criativas Mensais Contratadas: {cliente['n_monthly_contracted_creative_mandalecas']}")
        st.write(f"Mandaleças de Adaptação de Formato Mensais Contratadas: {cliente['n_monthly_contracted_format_adaptation_mandalecas']}")
        st.write(f"Mandaleças de Conteúdo Mensais Contratadas: {cliente['n_monthly_contracted_content_mandalecas']}")
        st.write(f"Mandaleças Criativas Acumuladas: {cliente['accumulated_creative_mandalecas']}")
        st.write(f"Mandaleças de Adaptação de Formato Acumuladas: {cliente['accumulated_format_adaptation_mandalecas']}")
        st.write(f"Mandaleças de Conteúdo Acumuladas: {cliente['accumulated_content_mandalecas']}")

# Main logic to select a client and display their details
def main():
    st.sidebar.title("Selecione um Cliente")
    clientes_df = get_clientes()
    cliente_id = st.sidebar.selectbox("Clientes", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])
    if cliente_id:
        show_cliente(cliente_id)

if __name__ == "__main__":
    main()
