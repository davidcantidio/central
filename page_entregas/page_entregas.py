import streamlit as st
import pandas as pd
import logging
from sqlalchemy.orm import Session
from common.models import AttentionPoints, Client
from datetime import datetime
import locale
from streamlit_modal import Modal
from page_entregas.attention_points.attention_points_modal import add_attention_point_modal
from page_entregas.attention_points.attention_points_table import display_attention_points_table
# Configurar a localidade para português do Brasil
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')  # Para Windows

# Configuração de logging
logging.basicConfig(filename='debug_log.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações iniciais do Streamlit
st.set_page_config(layout="wide")

def page_entregas(engine):
    logging.debug("Entrando na função page_entregas()")

    # ===========================================================
    # Seção de Seletores de Cliente e Intervalo de Datas na Barra Lateral
    # ===========================================================

    st.sidebar.title("Filtros")

    # Obter a lista de clientes
    clientes_df = get_clientes(engine)

    # Verificar se há clientes disponíveis
    if clientes_df.empty:
        st.error("Nenhum cliente disponível.")
        return

    # Inicializar o st.session_state para data_inicio e data_fim, se necessário
    if "data_inicio" not in st.session_state:
        st.session_state["data_inicio"] = datetime.today() - pd.Timedelta(days=30)
    if "data_fim" not in st.session_state:
        st.session_state["data_fim"] = datetime.today()
    if "cliente_id" not in st.session_state:
        st.session_state["cliente_id"] = clientes_df["id"].iloc[0]

    # Criar um formulário na barra lateral para os seletores
    with st.sidebar.form(key='filters_form'):
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
            st.rerun()
        else:
            st.error("Por favor, selecione um intervalo de datas válido.")

    # Log dos valores selecionados
    logging.debug(f"Cliente selecionado: {st.session_state['cliente_id']}")
    logging.debug(f"Data início: {st.session_state['data_inicio']}, Data fim: {st.session_state['data_fim']}")

    # Obter o nome do cliente selecionado
    cliente_nome = clientes_df[clientes_df["id"] == st.session_state["cliente_id"]]["name"].values[0]

    # Exibir o nome do cliente selecionado na página principal
    st.write(f"## Cliente Selecionado: {cliente_nome}")

    # ===========================================================
    # Botão para adicionar ponto de atenção
    # ===========================================================

    add_attention_point_modal(engine)
    # ===========================================================
    # Exibir Pontos de Atenção
    # ===========================================================

    st.write("### Pontos de Atenção")
    display_attention_points_table(
        st.session_state["cliente_id"],
        st.session_state["data_inicio"],
        st.session_state["data_fim"],
        engine
    )

# Função para obter a lista de clientes do banco de dados
def get_clientes(engine):
    with Session(bind=engine) as session:
        clientes = session.query(Client).all()
        clientes_df = pd.DataFrame([{'id': c.id, 'name': c.name} for c in clientes])
    return clientes_df


# ===========================================================
# Função principal para executar a página
# ===========================================================
if __name__ == "__main__":
    from common.database import create_engine_and_session
    engine = create_engine_and_session()

    # Executar a função principal
    page_entregas(engine)
