import streamlit as st
from streamlit_option_menu import option_menu
from page_home_logic import home
from page_client_logic import show_cliente, get_clientes
import pandas as pd
from process_xlsx import process_xlsx_file
import logging
import os
from sqlalchemy import create_engine
from page_entregas.page_entregas import page_entregas as entregas_logic

# Configurações de logging
LOG_FILE = 'process_xlsx.log'

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Criação de fallback de log para exibir na consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logging.debug("Iniciando aplicação")

# Inicializar o engine do banco de dados
DATABASE_URL = 'sqlite:///common/db_mandala.sqlite'
engine = create_engine(DATABASE_URL)

# Função para exibir as páginas secundárias
def show_secondary_page(page, cliente_id, start_date, end_date):
    logging.debug(f"Exibindo página secundária: {page}, Cliente: {cliente_id}")
    st.write(f"DEBUG: Exibindo página secundária: {page}, Cliente: {cliente_id}")
    # Conteúdo baseado na página
    # ...

# Lógica principal
def main():
    logging.debug("Entrando na função principal.")
    st.sidebar.title("Menu")

    # Inicializa 'data_inicio' e 'data_fim' no session_state se não estiverem definidos
    if "data_inicio" not in st.session_state:
        st.session_state["data_inicio"] = pd.to_datetime("2023-01-01")
    if "data_fim" not in st.session_state:
        st.session_state["data_fim"] = pd.to_datetime("2023-12-31")

    clientes_df = get_clientes()

    if "cliente_id" not in st.session_state:
        st.session_state["cliente_id"] = clientes_df["id"][0] if not clientes_df.empty else None

    menu = option_menu(
        menu_title=None,
        options=["Home", "Clientes", "Entregas"],
        icons=["house", "people", "box"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )
    logging.debug(f"Menu selecionado: {menu}")

    if menu == "Home":
        logging.debug("Exibindo página Home")
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        home()
        st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Clientes":
        logging.debug("Exibindo página Clientes")

        cliente_id = st.sidebar.selectbox(
            "Clientes", 
            clientes_df['id'], 
            format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0]
        )

        st.session_state["cliente_id"] = cliente_id

        col1, col2 = st.sidebar.columns(2)
        with col1:
            data_inicio = st.date_input("Data de início", value=st.session_state["data_inicio"], key="data_inicio")
        with col2:
            data_fim = st.date_input("Data de fim", value=st.session_state["data_fim"], key="data_fim")

        # Não devemos atribuir diretamente a st.session_state após criar os widgets
        # Remova as seguintes linhas:
        # st.session_state["data_inicio"] = data_inicio
        # st.session_state["data_fim"] = data_fim

        submenu = option_menu(
            menu_title="Clientes",
            options=["Início", "Briefings", "Planos", "Campanhas"],
            icons=["house", "file-text", "map", "bullhorn"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

        if submenu == "Início":
            st.markdown("<div class='container'>", unsafe_allow_html=True)
            show_cliente(
                cliente_id,
                st.session_state["data_inicio"],
                st.session_state["data_fim"]
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='container'>", unsafe_allow_html=True)
            show_secondary_page(
                submenu,
                cliente_id,
                st.session_state["data_inicio"],
                st.session_state["data_fim"]
            )
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Entregas":
        if "cliente_id" in st.session_state and st.session_state["cliente_id"]:
            logging.debug("Exibindo página Entregas")
            st.markdown("<div class='container'>", unsafe_allow_html=True)
            entregas_logic(engine)  # Passa o engine como argumento
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            logging.error("Nenhum cliente foi selecionado para visualização de entregas.")
            st.error("Selecione um cliente para visualizar as entregas.")

if __name__ == "__main__":
    main()
