import streamlit as st
import pandas as pd
import logging
from sqlalchemy.orm import Session
from common.models import AttentionPoints, Client, DeliveryCategoryEnum
from datetime import datetime, date, timedelta
import locale
from streamlit_modal import Modal
from page_entregas.attention_points.attention_points_table import display_attention_points_table
from page_entregas.content_production.content_production_table import display_content_production_table
from page_entregas.content_production.content_production_gauge import display_content_production_gauge
from page_entregas.utils.mandalecas import calcular_mandalecas
from streamlit_extras.stylable_container import stylable_container

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
        st.session_state["data_inicio"] = date.today() - timedelta(days=30)
    if "data_fim" not in st.session_state:
        st.session_state["data_fim"] = date.today()
    if "cliente_id" not in st.session_state:
        st.session_state["cliente_id"] = clientes_df["id"].iloc[0]

    # Criar um formulário na barra lateral para os seletores
    with st.sidebar.form(key='filters_form'):
        # Seletor de Cliente
        options = clientes_df["id"].tolist()

        # Usar st.session_state["cliente_id"] como valor inicial para manter a seleção atual
        cliente_id = st.selectbox(
            "Selecione o Cliente",
            options=options,
            index=options.index(st.session_state["cliente_id"]),
            format_func=lambda x: clientes_df[clientes_df["id"] == x]["name"].values[0],
            key="cliente_id_temp"  # Usar uma chave temporária para o seletor
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
        # Atualizar o cliente selecionado no session_state
        st.session_state["cliente_id"] = cliente_id
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
    cliente_logo_url = clientes_df[clientes_df["id"] == st.session_state["cliente_id"]]["logo_url"].values[0]

    # Exibir o nome do cliente selecionado na página principal
    if cliente_logo_url:
        col1, col2 = st.columns([1, 5])  # Ajuste as proporções das colunas conforme necessário

        with col1:
            st.image(cliente_logo_url, width=50)  # Exibe a logo do cliente com uma largura ajustada
        with col2:
            st.write(f"## {cliente_nome}")
    else:
        st.write(f"## {cliente_nome}")

    # Converter datas para datetime.datetime, se necessário
    data_inicio_datetime = datetime.combine(st.session_state["data_inicio"], datetime.min.time())
    data_fim_datetime = datetime.combine(st.session_state["data_fim"], datetime.max.time())

    # ===========================================================
    # Exibir Pontos de Atenção
    # ===========================================================

    display_attention_points_table(
        st.session_state["cliente_id"],
        data_inicio_datetime,
        data_fim_datetime,
        engine
    )

    # ===========================================================
    # Seção de Produção de Conteúdo
    # ===========================================================

    # Obter os valores de mandalecas reais
    with Session(bind=engine) as session:
        mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(
            st.session_state["cliente_id"],
            data_inicio_datetime,
            data_fim_datetime,
            session
        )

    # Exibir o container com o gráfico e a tabela
    st.write("**Produção de Conteúdo**")
    with stylable_container(
        key="content_production_section",
        css_styles="""
        {
            background-color: white;
            padding: 15px;
            border: 2px solid gray;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        """
    ):
        # Botão para adicionar nova produção de conteúdo
        if st.button("Adicionar Produção de Conteúdo"):
            st.session_state["show_content_production_form"] = True

        # Exibir o formulário em um modal, se o botão for clicado
        if st.session_state.get("show_content_production_form", False):
            display_content_production_form(
                st.session_state["cliente_id"],
                engine
            )

        # Criar colunas para o gráfico e a tabela
        col_gauge, col_table = st.columns([1, 2])  # 30% e 70%

        with col_gauge:
            # Exibir o gráfico de gauge para produção de conteúdo
            display_content_production_gauge(
                mandalecas_contratadas,
                mandalecas_usadas,
                mandalecas_acumuladas
            )

        with col_table:
            # Exibir a tabela de produção de conteúdo
            display_content_production_table(
                st.session_state["cliente_id"],
                data_inicio_datetime,
                data_fim_datetime,
                engine
            )

    # ===========================================================
    # Outras Seções (se houver)
    # ===========================================================

# Função para obter a lista de clientes do banco de dados
def get_clientes(engine):
    with Session(bind=engine) as session:
        clientes = session.query(Client).all()
        clientes_df = pd.DataFrame([{'id': c.id, 'name': c.name, 'logo_url': c.logo_url} for c in clientes])
    return clientes_df

# ===========================================================
# Função principal para executar a página
# ===========================================================
if __name__ == "__main__":
    from common.database import create_engine_and_session
    engine = create_engine_and_session()

    # Executar a função principal
    page_entregas(engine)
