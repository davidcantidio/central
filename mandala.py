import streamlit as st
from streamlit_option_menu import option_menu
from page_home_logic import home
from page_criacao_logic import page_criacao
from page_client_logic import show_cliente, get_clientes
import pandas as pd


# Função para exibir as páginas secundárias
def show_secondary_page(page, cliente_id, start_date, end_date):
    if page == "Tráfego Pago":
        st.title("Tráfego Pago")
        st.write("Conteúdo para Tráfego Pago")
    elif page == "Assessoria":
        st.title("Assessoria")
        st.write("Conteúdo para Assessoria")
    elif page == "Criação":
        # Definindo o cliente selecionado para a página de criação
        cliente_selecionado = None
        page_criacao(cliente_selecionado)
    elif page == "Redes Sociais":
        st.title("Redes Sociais")
        st.write("Conteúdo para Redes Sociais")

# Lógica principal
def main():
    st.sidebar.title("Menu")
    menu = option_menu(
        menu_title=None,
        options=["Home", "Tráfego Pago", "Assessoria", "Criação", "Redes Sociais"],
        icons=["house", "graph-up", "briefcase", "palette", "globe"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    # Seleção do cliente e intervalo de datas
    clientes_df = get_clientes()
    cliente_id = st.sidebar.selectbox("Clientes", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])

    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio = st.date_input("Data de início", value=pd.to_datetime("2023-01-01"), key="data_inicio")
    with col2:
        data_fim = st.date_input("Data de fim", value=pd.to_datetime("2023-12-31"), key="data_fim")

    st.session_state["cliente_id"] = cliente_id

    if menu == "Home":
        show_cliente(cliente_id, data_inicio, data_fim)
    else:
        show_secondary_page(menu, cliente_id, data_inicio, data_fim)

if __name__ == "__main__":
    main()
