import streamlit as st
from streamlit_option_menu import option_menu
from page_home_logic import home
from page_criacao_logic import page_criacao
from page_client_logic import show_cliente, get_clientes
import pandas as pd
from process_xlsx import process_xlsx_file
import logging

# Configura o log
logging.basicConfig(filename='process_xlsx.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para exibir as páginas secundárias
def show_secondary_page(page, cliente_id, start_date, end_date):
    if page == "Início":
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        st.title("Início")
        st.write("Conteúdo para Início")
        st.markdown("</div>", unsafe_allow_html=True)
    elif page == "Briefings":
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        st.title("Briefings")
        st.write("Conteúdo para Briefings")
        st.markdown("</div>", unsafe_allow_html=True)
    elif page == "Planos":
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        st.title("Planos")
        st.write("Conteúdo para Planos")
        st.markdown("</div>", unsafe_allow_html=True)
    elif page == "Campanhas":
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        st.title("Campanhas")
        st.write("Conteúdo para Campanhas")
        st.markdown("</div>", unsafe_allow_html=True)

# Lógica principal
def main():

    st.sidebar.title("Menu")
    menu = option_menu(
        menu_title=None,
        options=["Home", "Clientes", "Entregas"],
        icons=["house", "people", "box"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    if menu == "Home":
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        home()
        st.markdown("</div>", unsafe_allow_html=True)
    elif menu == "Clientes":
        submenu = option_menu(
            menu_title="Clientes",
            options=["Início", "Briefings", "Planos", "Campanhas"],
            icons=["house", "file-text", "map", "bullhorn"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

        clientes_df = get_clientes()
        cliente_id = st.sidebar.selectbox("Clientes", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])

        col1, col2 = st.sidebar.columns(2)
        with col1:
            data_inicio = st.date_input("Data de início", value=pd.to_datetime("2023-01-01"), key="data_inicio")
        with col2:
            data_fim = st.date_input("Data de fim", value=pd.to_datetime("2023-12-31"), key="data_fim")

        st.session_state["cliente_id"] = cliente_id

        if submenu == "Início":
            st.markdown("<div class='container'>", unsafe_allow_html=True)
            show_cliente(cliente_id, data_inicio, data_fim)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='container'>", unsafe_allow_html=True)
            show_secondary_page(submenu, cliente_id, data_inicio, data_fim)
            st.markdown("</div>", unsafe_allow_html=True)
    elif menu == "Entregas":
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        page_criacao()
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
