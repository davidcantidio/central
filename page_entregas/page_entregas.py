import streamlit as st
from streamlit_option_menu import option_menu
from page_home_logic import home
from page_client_logic import show_cliente, get_clientes
import pandas as pd
from process_xlsx import process_xlsx_file
import logging

# Importações das funções dentro da pasta page_entregas
from page_entregas.attention_points.attention_points_table import display_attention_points_table
from page_entregas.attention_points.attention_points_modal import modal_attention_point_open
from page_entregas.content_production.content_production_table import display_content_production_table
from page_entregas.content_production.content_production_modal import modal_content_production_open
from page_entregas.creation_and_adaptation.creation_gauge import display_creation_gauge
from page_entregas.creation_and_adaptation.adaptation_gauge import display_adaptation_gauge
from page_entregas.guidance_status.guidance_modal import display_guidance_modal
from page_entregas.guidance_status.guidance_timeline import display_guidance_timeline
from page_entregas.paid_traffic.traffic_gauge import display_traffic_gauge
from page_entregas.plan_status.plan_modal import display_plan_modal
from page_entregas.plan_status.plan_timeline import display_plan_timeline
from page_entregas.social_media.social_media_gauges import display_other_networks_gauge
from page_entregas.website_maintenance.website_gauge_timeline import display_website_maintenance_gauge_and_timeline
from page_entregas.utils.mandalecas import calcular_mandalecas

# Configuração de logging
logging.basicConfig(filename='debug_log.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Adicionando uma linha para verificar se o arquivo de log está funcionando
logging.debug("Arquivo de log inicializado!")

# Configurações iniciais do Streamlit
st.set_page_config(layout="wide")

# Função para organizar e exibir a página de entregas
def page_entregas():
    logging.debug("Entrando na função page_entregas()")
    st.write("DEBUG: Entrou na função `page_entregas()`")  # Verificar na interface
    if "cliente_id" not in st.session_state or st.session_state["cliente_id"] is None:
        logging.warning("Nenhum cliente selecionado. Exibindo mensagem de erro.")
        st.write("Nenhum cliente selecionado!")  # Verificar na interface
        st.error("Selecione um cliente para visualizar as entregas.")
        return

    cliente_id = st.session_state["cliente_id"]
    logging.debug(f"Cliente selecionado: {cliente_id}")
    st.write(f"Cliente selecionado: {cliente_id}")  # Verificar na interface

    # Definir data de início e fim
    data_inicio = st.session_state.get("data_inicio", pd.to_datetime("2023-01-01"))
    data_fim = st.session_state.get("data_fim", pd.to_datetime("2023-12-31"))
    logging.debug(f"Data início: {data_inicio}, Data fim: {data_fim}")
    st.write(f"Datas selecionadas: {data_inicio} até {data_fim}")  # Verificar na interface

    # Exibir tabela de pontos de atenção
    logging.debug("Exibindo tabela de pontos de atenção")
    st.write("Exibindo pontos de atenção...")  # Verificar na interface
    display_attention_points_table(cliente_id, data_inicio, data_fim)
    modal_attention_point_open()

    # Exibir produção de conteúdo
    logging.debug("Exibindo tabela de produção de conteúdo")
    st.write("Exibindo produção de conteúdo...")  # Verificar na interface
    display_content_production_table(cliente_id)
    modal_content_production_open()

    # Calcular mandalecas
    logging.debug("Calculando mandalecas")
    st.write("Calculando mandalecas...")  # Verificar na interface
    mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

    # Exibir gauges de criação e adaptação
    logging.debug("Exibindo gauge de criação e adaptação")
    st.write("Exibindo gauges de criação e adaptação...")  # Verificar na interface
    display_creation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_adaptation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir gauge de tráfego pago
    logging.debug("Exibindo gauge de tráfego pago")
    st.write("Exibindo gauge de tráfego pago...")  # Verificar na interface
    display_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir plano e direcionamento
    logging.debug("Exibindo timeline de plano e modal")
    st.write("Exibindo timeline de plano e modal...")  # Verificar na interface
    display_plan_timeline(cliente_id)
    display_plan_modal(cliente_id)
    display_guidance_timeline(cliente_id)
    display_guidance_modal(cliente_id)

    # Exibir social media gauges
    logging.debug("Exibindo gauges de redes sociais")
    st.write("Exibindo gauges de redes sociais...")  # Verificar na interface
    display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir gauge e timeline de manutenção de website
    logging.debug("Exibindo gauge e timeline de manutenção de website")
    st.write("Exibindo gauge e timeline de manutenção de website...")  # Verificar na interface
    display_website_maintenance_gauge_and_timeline(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

# Função para organizar e exibir a página de clientes
def page_clientes():
    logging.debug("Entrando na função page_clientes()")
    st.write("DEBUG: Entrou na função `page_clientes()`")  # Verificar na interface
    st.markdown("<h2>Clientes</h2>", unsafe_allow_html=True)

    clientes_df = get_clientes()
    logging.debug(f"Clientes carregados: {len(clientes_df)}")
    st.write(f"Clientes carregados: {len(clientes_df)}")  # Verificar na interface

    if clientes_df.empty:
        logging.error("Nenhum cliente disponível.")
        st.error("Nenhum cliente disponível.")
        return

    # Selecionar o cliente e armazenar no session_state
    cliente_id = st.selectbox(
        "Selecione o Cliente",
        clientes_df['id'],
        format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0],
    )
    st.session_state["cliente_id"] = cliente_id
    logging.debug(f"Cliente selecionado e armazenado no session_state: {cliente_id}")
    st.write(f"Cliente selecionado: {cliente_id}")  # Verificar na interface

    # Definir datas de início e fim no session_state
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data de início", value=pd.to_datetime("2023-01-01"), key="data_inicio")
    with col2:
        data_fim = st.date_input("Data de fim", value=pd.to_datetime("2023-12-31"), key="data_fim")

    st.session_state["data_inicio"] = data_inicio
    st.session_state["data_fim"] = data_fim
    logging.debug(f"Datas armazenadas no session_state: Início - {data_inicio}, Fim - {data_fim}")
    st.write(f"Datas armazenadas: {data_inicio} até {data_fim}")  # Verificar na interface

    # Exibir informações do cliente selecionado
    logging.debug(f"Exibindo informações do cliente {cliente_id}")
    st.write(f"Exibindo informações do cliente {cliente_id}")  # Verificar na interface
    show_cliente(cliente_id, data_inicio, data_fim)

# Lógica principal
def main():
    logging.debug("Iniciando aplicação principal")
    st.write("DEBUG: Aplicação iniciada!")  # Verificar na interface
    st.sidebar.title("Menu")
    menu = option_menu(
        menu_title=None,
        options=["Home", "Clientes", "Entregas"],
        icons=["house", "people", "box"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )
    logging.debug(f"Menu selecionado: {menu}")
    st.write(f"Menu selecionado: {menu}")  # Verificar na interface

    if menu == "Home":
        logging.debug("Entrando na página Home")
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        home()
        st.markdown("</div>", unsafe_allow_html=True)
    elif menu == "Clientes":
        logging.debug("Entrando na página Clientes")
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        page_clientes()
        st.markdown("</div>", unsafe_allow_html=True)
    elif menu == "Entregas":
        logging.debug("Entrando na página Entregas")
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        page_entregas()
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
