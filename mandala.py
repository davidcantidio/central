import streamlit as st
from streamlit_option_menu import option_menu
from page_home_logic import home
from page_criacao_logic import page_criacao
from page_client_logic import show_cliente
# Função para exibir as páginas secundárias
def show_secondary_page(page):
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

    if "cliente_id" in st.session_state and menu == "Home":
        show_cliente(st.session_state["cliente_id"])
    elif menu == "Home":
        home()
    elif menu in ["Tráfego Pago", "Assessoria", "Criação", "Redes Sociais"]:
        show_secondary_page(menu)

if __name__ == "__main__":
    main()
