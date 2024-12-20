import streamlit as st
import pandas as pd
import logging
from sqlalchemy.orm import Session
from common.models import AttentionPoints, Client
from datetime import datetime, date, timedelta
import locale
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

    # Obter o cliente selecionado e armazenar no st.session_state
    with Session(bind=engine) as session:
        cliente_selecionado = session.query(Client).filter(Client.id == st.session_state["cliente_id"]).first()
        if cliente_selecionado:
            st.session_state["cliente_obj"] = cliente_selecionado
        else:
            st.error("Cliente não encontrado.")
            return

    # Obter o nome do cliente selecionado e formatar com mês/ano
    cliente_nome = cliente_selecionado.name
    cliente_logo_url = cliente_selecionado.logo_url
    mes_ano = st.session_state["data_fim"].strftime('%B/%y').capitalize()

    # Exibir o nome do cliente seguido do mês e ano na página principal
    if cliente_logo_url:
        col1, col2 = st.columns([1, 5])  # Ajuste as proporções das colunas conforme necessário

        with col1:
            st.image(cliente_logo_url, width=50)  # Exibe a logo do cliente com uma largura ajustada
        with col2:
            st.write(f"## {cliente_nome} : {mes_ano}")
    else:
        st.write(f"## {cliente_nome} : {mes_ano}")

    # ============================================
    # Exibir Pontos de Atenção (Attention Points)
    # ============================================
    with stylable_container(
        key="attention_points_section",
        css_styles="""
        {
            margin-bottom: 45px;
            background-color: #fff;
            padding: 15px;
            border-radius: 10px;
        }
        """
    ):
        display_attention_points_table(
            st.session_state["cliente_id"],
            st.session_state["data_inicio"],
            st.session_state["data_fim"],
            engine
        )

    # ============================================
    # Exibir Produção de Conteúdo (Content Production)
    # ============================================
    with stylable_container(
        key="content_production_section",
        css_styles="""
        {
            margin-bottom: 45px;
            background-color: #fff;
            padding: 15px;
            border-radius: 10px;
        }
        """
    ):
        # Calcular mandalecas para o gauge de produção de conteúdo
        with Session(bind=engine) as session:
            mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas = calcular_mandalecas(
                st.session_state["cliente_obj"],
                st.session_state["data_inicio"],
                st.session_state["data_fim"],
                session
            )

        # Criar colunas para o gauge e a tabela
        col_gauge, col_table = st.columns([0.3, 0.7])

        with col_gauge:
            # Exibir o gauge de Produção de Conteúdo
            display_content_production_gauge(
                mandalecas_contratadas,
                mandalecas_usadas,
                mandalecas_acumuladas,
                engine
            )

        with col_table:
            # Exibir a tabela de Produção de Conteúdo
            display_content_production_table(
                st.session_state["cliente_id"],
                st.session_state["data_inicio"],
                st.session_state["data_fim"],
                engine
            )

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
