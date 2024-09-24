import streamlit as st
import pandas as pd
import logging
from streamlit_modal import Modal

# Importações das funções dentro da pasta page_entregas
from page_entregas.attention_points.attention_points_table import display_attention_points_table
from page_entregas.attention_points.attention_points_modal import modal_attention_point_open
# from page_entregas.content_production.content_production_table import display_content_production_table
# from page_entregas.content_production.content_production_modal import modal_content_production_open
# from page_entregas.creation_and_adaptation.creation_gauge import display_creation_gauge
# from page_entregas.creation_and_adaptation.adaptation_gauge import display_adaptation_gauge
# from page_entregas.guidance_status.guidance_modal import display_guidance_modal
# from page_entregas.guidance_status.guidance_timeline import display_guidance_timeline
# from page_entregas.paid_traffic.traffic_gauge import display_traffic_gauge
# from page_entregas.plan_status.plan_modal import display_plan_modal
# from page_entregas.plan_status.plan_timeline import display_plan_timeline
# from page_entregas.social_media.social_media_gauges import display_other_networks_gauge
# from page_entregas.website_maintenance.website_gauge_timeline import display_website_maintenance_gauge_and_timeline
# from page_entregas.utils.mandalecas import calcular_mandalecas

# Configuração de logging
logging.basicConfig(filename='debug_log.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações iniciais do Streamlit
st.set_page_config(layout="wide")

# Função para organizar e exibir a página de entregas
def page_entregas(engine):
    logging.debug("Entrando na função page_entregas()")

    if "cliente_id" not in st.session_state or st.session_state["cliente_id"] is None:
        logging.warning("Nenhum cliente selecionado. Exibindo mensagem de erro.")
        st.error("Selecione um cliente para visualizar as entregas.")
        return

    cliente_id = st.session_state["cliente_id"]
    logging.debug(f"Cliente selecionado: {cliente_id}")

    # Definir data de início e fim
    data_inicio = st.session_state.get("data_inicio", pd.to_datetime("2023-01-01"))
    data_fim = st.session_state.get("data_fim", pd.to_datetime("2023-12-31"))
    logging.debug(f"Data início: {data_inicio}, Data fim: {data_fim}")

    # ===========================================================
    # Seção de Pontos de Atenção
    # ===========================================================
    # Exibir tabela de pontos de atenção
    logging.debug("Exibindo tabela de pontos de atenção")
    display_attention_points_table(cliente_id, data_inicio, data_fim, engine)

    # Inicializar o modal para adicionar ponto de atenção
    modal = Modal("Adicionar Ponto de Atenção", key="adicionar-ponto-modal", max_width=800)

    # Botão para abrir o modal
    if st.button("Adicionar Ponto de Atenção"):
        modal.open()
        logging.debug("Botão 'Adicionar Ponto de Atenção' clicado. Modal aberto.")

    # Verifica se o modal está aberto
    if modal.is_open():
        # Chamar a função que exibe o conteúdo do modal
        modal_attention_point_open(engine, modal)

    # ===========================================================
    # As seguintes seções estão comentadas para isolar o problema
    # ===========================================================

    # # ===========================================================
    # # Seção de Produção de Conteúdo
    # # ===========================================================
    # # Exibir tabela de produção de conteúdo
    # logging.debug("Exibindo tabela de produção de conteúdo")
    # display_content_production_table(cliente_id)

    # # Inicializar o modal para adicionar produção de conteúdo
    # content_modal = Modal("Adicionar Produção de Conteúdo", key="adicionar-producao-modal", max_width=800)

    # # Botão para abrir o modal de produção de conteúdo
    # if st.button("Adicionar Produção de Conteúdo"):
    #     content_modal.open()
    #     logging.debug("Botão 'Adicionar Produção de Conteúdo' clicado. Modal aberto.")

    # # Verifica se o modal está aberto
    # if content_modal.is_open():
    #     # Chamar a função que exibe o conteúdo do modal
    #     modal_content_production_open(cliente_id, content_modal)

    # # ===========================================================
    # # Cálculo de Mandalecas
    # # ===========================================================
    # logging.debug("Calculando mandalecas")
    # mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(cliente_id)

    # # ===========================================================
    # # Seção de Criação e Adaptação
    # # ===========================================================
    # logging.debug("Exibindo gauges de criação e adaptação")
    # display_creation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)
    # display_adaptation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # # ===========================================================
    # # Seção de Tráfego Pago
    # # ===========================================================
    # logging.debug("Exibindo gauge de tráfego pago")
    # display_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # # ===========================================================
    # # Seção de Plano e Direcionamento
    # # ===========================================================
    # logging.debug("Exibindo timeline de plano e modal")
    # display_plan_timeline(cliente_id)
    # display_plan_modal(cliente_id)
    # display_guidance_timeline(cliente_id)
    # display_guidance_modal(cliente_id)

    # # ===========================================================
    # # Seção de Redes Sociais
    # # ===========================================================
    # logging.debug("Exibindo gauges de redes sociais")
    # display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas)

    # # ===========================================================
    # # Seção de Manutenção de Website
    # # ===========================================================
    # logging.debug("Exibindo gauge e timeline de manutenção de website")
    # # Você deve obter as datas de manutenção necessárias
    # maintenance_dates = []  # Substitua por suas datas reais
    # display_website_maintenance_gauge_and_timeline(
    #     mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, maintenance_dates
    # )
