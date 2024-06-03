import streamlit as st
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu

# Função para obter clientes do banco de dados
def get_clientes():
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        df = pd.read_sql_query("SELECT * FROM clients", conn)
    return df

# Função para atualizar o cliente no banco de dados
def update_cliente(cliente_id, updated_data):
    with sqlite3.connect('common/db_mandala.sqlite') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clients
            SET name = ?, 
                n_monthly_contracted_creative_mandalecas = ?, 
                n_monthly_contracted_format_adaptation_mandalecas = ?, 
                n_monthly_contracted_content_production_mandalecas = ?, 
                accumulated_creative_mandalecas = ?, 
                accumulated_format_adaptation_mandalecas = ?, 
                accumulated_content_mandalecas = ?
            WHERE id = ?
        """, (
            updated_data['name'], 
            updated_data['n_monthly_contracted_creative_mandalecas'], 
            updated_data['n_monthly_contracted_format_adaptation_mandalecas'], 
            updated_data['n_monthly_contracted_content_production_mandalecas'], 
            updated_data['accumulated_creative_mandalecas'], 
            updated_data['accumulated_format_adaptation_mandalecas'], 
            updated_data['accumulated_content_mandalecas'], 
            cliente_id
        ))
        conn.commit()

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
        name = st.text_input("Nome", cliente['name'])
        n_monthly_contracted_creative_mandalecas = st.number_input("Mandaleças Criativas Mensais Contratadas", value=cliente['n_monthly_contracted_creative_mandalecas'])
        n_monthly_contracted_format_adaptation_mandalecas = st.number_input("Mandaleças de Adaptação de Formato Mensais Contratadas", value=cliente['n_monthly_contracted_format_adaptation_mandalecas'])
        n_monthly_contracted_content_production_mandalecas = st.number_input("Mandaleças de Conteúdo Mensais Contratadas", value=cliente['n_monthly_contracted_content_production_mandalecas'])
        accumulated_creative_mandalecas = st.number_input("Mandaleças Criativas Acumuladas", value=cliente['accumulated_creative_mandalecas'])
        accumulated_format_adaptation_mandalecas = st.number_input("Mandaleças de Adaptação de Formato Acumuladas", value=cliente['accumulated_format_adaptation_mandalecas'])
        accumulated_content_mandalecas = st.number_input("Mandaleças de Conteúdo Acumuladas", value=cliente['accumulated_content_mandalecas'])

        if st.button("Atualizar"):
            if not name:
                st.error("O campo 'Nome' não pode ficar em branco.")
            else:
                updated_data = {
                    'name': name,
                    'n_monthly_contracted_creative_mandalecas': n_monthly_contracted_creative_mandalecas,
                    'n_monthly_contracted_format_adaptation_mandalecas': n_monthly_contracted_format_adaptation_mandalecas,
                    'n_monthly_contracted_content_production_mandalecas': n_monthly_contracted_content_production_mandalecas,
                    'accumulated_creative_mandalecas': accumulated_creative_mandalecas,
                    'accumulated_format_adaptation_mandalecas': accumulated_format_adaptation_mandalecas,
                    'accumulated_content_mandalecas': accumulated_content_mandalecas
                }
                update_cliente(cliente_id, updated_data)
                st.success("Dados do cliente atualizados com sucesso!")

# Main logic to select a client and display their details
def main():
    st.sidebar.title("Selecione um Cliente")
    clientes_df = get_clientes()
    cliente_id = st.sidebar.selectbox("Clientes", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])
    if cliente_id:
        show_cliente(cliente_id)

if __name__ == "__main__":
    main()
