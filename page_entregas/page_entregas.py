import streamlit as st
import pandas as pd
import logging
from streamlit_modal import Modal
from streamlit_extras.stylable_container import stylable_container  # Importe o stylable_container
from page_entregas.attention_points.attention_points_table import display_attention_points_table
from page_entregas.attention_points.attention_points_modal import modal_attention_point_open
from page_client_logic import get_clientes

# Configuração de logging
logging.basicConfig(filename='debug_log.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações iniciais do Streamlit
st.set_page_config(layout="wide")

def page_entregas(engine):
    logging.debug("Entrando na função page_entregas()")

    # ===========================================================
    # Seção de Seletores de Cliente e Intervalo de Datas
    # ===========================================================

    # Obter a lista de clientes
    clientes_df = get_clientes()

    # Verificar se há clientes disponíveis
    if clientes_df.empty:
        st.error("Nenhum cliente disponível.")
        return

    # Inicializar o st.session_state para data_inicio e data_fim, se necessário
    if "data_inicio" not in st.session_state:
        st.session_state["data_inicio"] = pd.to_datetime("2023-01-01")
    if "data_fim" not in st.session_state:
        st.session_state["data_fim"] = pd.to_datetime("2023-12-31")
    if "cliente_id" not in st.session_state:
        st.session_state["cliente_id"] = clientes_df["id"].iloc[0]

    # Criar um formulário para os seletores
    with st.form(key='filters_form'):
        col1, col2 = st.columns([2, 2])

        with col1:
            # Seletor de Cliente
            options = clientes_df["id"].tolist()
            selected_index = clientes_df[clientes_df["id"] == st.session_state["cliente_id"]].index[0]
            selected_index = int(selected_index)  # Garantir que seja um int nativo

            cliente_id = st.selectbox(
                "Selecione o Cliente",
                options=options,
                index=selected_index,
                format_func=lambda x: clientes_df[clientes_df["id"] == x]["name"].values[0],
                key="cliente_id"
            )

        with col2:
            # Seletor de Intervalo de Datas
            date_range = st.date_input(
                "Selecione o Intervalo de Datas",
                value=(st.session_state["data_inicio"], st.session_state["data_fim"]),
                key="date_range"
            )

        # Botão para aplicar os filtros
        submit_button = st.form_submit_button(label='Aplicar Filtros')

    # Verifica se o botão foi clicado
    if submit_button:
        # Validar o intervalo de datas
        if isinstance(date_range, tuple) and len(date_range) == 2:
            data_inicio, data_fim = date_range
            # Atualizar o st.session_state com os valores selecionados
            st.session_state["data_inicio"] = data_inicio
            st.session_state["data_fim"] = data_fim
            logging.debug("Filtros aplicados. Reexecutando a página.")
            # Reexecuta a página para atualizar os dados
            st.experimental_rerun()
        else:
            st.error("Por favor, selecione um intervalo de datas válido.")

    # Log dos valores selecionados
    logging.debug(f"Cliente selecionado: {st.session_state['cliente_id']}")
    logging.debug(f"Data início: {st.session_state['data_inicio']}, Data fim: {st.session_state['data_fim']}")

    # ===========================================================
    # Seção de Pontos de Atenção com Contêiner Estilizado
    # ===========================================================
    # Definir o estilo CSS do contêiner
    container_style = """
    {
        background-color: #FFFFFF;
        border-radius: 10px;
        border: 1px dashed gray;
        padding: 15px;
        margin-top: 15px;
        margin-bottom: 45px;
        margin-right: 15px;
    }
    """

    with stylable_container(key="attention_points_container", css_styles=container_style):
        st.write("### Pontos de Atenção")
        # Exibir tabela de pontos de atenção
        logging.debug("Exibindo tabela de pontos de atenção")
        display_attention_points_table(
            st.session_state["cliente_id"],
            st.session_state["data_inicio"],
            st.session_state["data_fim"],
            engine
        )

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
