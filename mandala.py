import streamlit as st
from streamlit_option_menu import option_menu
from page_home_logic import home
from page_client_logic import show_cliente, get_clientes
import pandas as pd
from process_xlsx import process_xlsx_file
import logging
import os

# Definir a criação do arquivo de log
LOG_FILE = 'process_xlsx.log'

# Verificar se o arquivo de log pode ser criado ou existe
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w').close()  # Criar o arquivo se não existir

# Configurações iniciais de logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Fallback logging: para garantir que algo será exibido, caso o arquivo de log falhe
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Adicionar fallback ao logger root
logging.getLogger().addHandler(console_handler)

# Teste inicial de log para verificar o funcionamento
logging.debug("Iniciando aplicação")

# Importações das funções dentro da pasta page_entregas
# Attention Points
from page_entregas.attention_points.attention_points_table import display_attention_points_table
from page_entregas.attention_points.attention_points_modal import modal_attention_point_open

# Content Production
from page_entregas.content_production.content_production_table import display_content_production_table
from page_entregas.content_production.content_production_modal import modal_content_production_open

# Creation and Adaptation Gauges
from page_entregas.creation_and_adaptation.creation_gauge import display_creation_gauge
from page_entregas.creation_and_adaptation.adaptation_gauge import display_adaptation_gauge

# Guidance
from page_entregas.guidance_status.guidance_modal import display_guidance_modal
from page_entregas.guidance_status.guidance_timeline import display_guidance_timeline

# Traffic Gauge
from page_entregas.paid_traffic.traffic_gauge import display_traffic_gauge

# Plan
from page_entregas.plan_status.plan_modal import display_plan_modal
from page_entregas.plan_status.plan_timeline import display_plan_timeline

# Social Media Gauges
from page_entregas.social_media.social_media_gauges import display_other_networks_gauge

# Website Gauge and Timeline
from page_entregas.website_maintenance.website_gauge_timeline import display_website_maintenance_gauge_and_timeline

# Função para calcular mandalecas
from page_entregas.utils.mandalecas import calcular_mandalecas


# Função para exibir as páginas secundárias
def show_secondary_page(page, cliente_id, start_date, end_date):
    logging.debug(f"Exibindo página secundária: {page}, Cliente: {cliente_id}")
    st.write(f"DEBUG: Exibindo página secundária: {page}, Cliente: {cliente_id}")
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


# Função para organizar e exibir a página de entregas
def page_entregas():
    logging.debug("Entrando na função page_entregas()")
    st.write("DEBUG: Entrou na função `page_entregas()`")

    # Verifique se o cliente foi selecionado
    if "cliente_id" not in st.session_state or st.session_state["cliente_id"] is None:
        logging.error("Nenhum cliente selecionado.")
        st.error("Selecione um cliente para visualizar as entregas.")
        return

    cliente_id = st.session_state["cliente_id"]
    logging.debug(f"Cliente selecionado: {cliente_id}")
    st.write(f"Cliente selecionado: {cliente_id}")

    # Definir data de início e fim a partir do session_state
    data_inicio = st.session_state.get("data_inicio", pd.to_datetime("2023-01-01"))
    data_fim = st.session_state.get("data_fim", pd.to_datetime("2023-12-31"))
    logging.debug(f"Data início: {data_inicio}, Data fim: {data_fim}")
    st.write(f"Datas selecionadas: {data_inicio} até {data_fim}")

    # Exibir tabela de pontos de atenção
    logging.debug("Exibindo tabela de pontos de atenção")
    display_attention_points_table(cliente_id, data_inicio, data_fim)
    modal_attention_point_open()

    # Exibir produção de conteúdo
    logging.debug("Exibindo tabela de produção de conteúdo")
    display_content_production_table(cliente_id)
    modal_content_production_open()

    # Calcular mandalecas
    logging.debug("Calculando mandalecas")
    mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

    # Exibir gauges de criação e adaptação
    logging.debug("Exibindo gauges de criação e adaptação")
    display_creation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    display_adaptation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir gauge de tráfego pago
    logging.debug("Exibindo gauge de tráfego pago")
    display_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir plano e direcionamento
    logging.debug("Exibindo plano e direcionamento")
    display_plan_timeline(cliente_id)
    display_plan_modal(cliente_id)
    display_guidance_timeline(cliente_id)
    display_guidance_modal(cliente_id)

    # Exibir social media gauges
    logging.debug("Exibindo gauges de redes sociais")
    display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # Exibir gauge e timeline de manutenção de website
    logging.debug("Exibindo gauge e timeline de manutenção de website")
    display_website_maintenance_gauge_and_timeline(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)


# Lógica principal
def main():
    logging.debug("Entrando na função principal.")
    st.sidebar.title("Menu")
    
    # Verificar se "data_inicio" e "data_fim" já estão no session_state
    if "data_inicio" not in st.session_state:
        st.session_state["data_inicio"] = pd.to_datetime("2023-01-01")
    if "data_fim" not in st.session_state:
        st.session_state["data_fim"] = pd.to_datetime("2023-12-31")
    
    # Exibir o menu de navegação
    menu = option_menu(
        menu_title=None,
        options=["Home", "Clientes", "Entregas"],
        icons=["house", "people", "box"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )
    logging.debug(f"Menu selecionado: {menu}")
    st.write(f"Menu selecionado: {menu}")

    # Página Home
    if menu == "Home":
        logging.debug("Exibindo página Home")
        st.markdown("<div class='container'>", unsafe_allow_html=True)
        home()
        st.markdown("</div>", unsafe_allow_html=True)

    # Página Clientes
    elif menu == "Clientes":
        logging.debug("Exibindo página Clientes")
        
        # Buscar lista de clientes
        clientes_df = get_clientes()
        logging.debug(f"Clientes disponíveis: {clientes_df}")

        # Criar seletor de cliente
        cliente_id = st.sidebar.selectbox("Clientes", clientes_df['id'], format_func=lambda x: clientes_df[clientes_df['id'] == x]['name'].values[0])
        
        # Armazenar o cliente selecionado no session_state
        st.session_state["cliente_id"] = cliente_id

