import re
import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControl, Client, Users
from common.database import engine
import plotly.graph_objects as go
from datetime import datetime
from process_xlsx import process_xlsx_file, identificar_categoria, extract_mandalecas
import logging


# Configura o log
logging.basicConfig(
    filename='process_xlsx.log',  # Nome do arquivo de log
    level=logging.INFO,           # Nível de log (INFO para registrar informações úteis)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato das mensagens de log
    datefmt='%Y-%m-%d %H:%M:%S'   # Formato da data e hora
)

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()

def display_gauge_chart(title, contracted, accumulated, used):
    max_value = contracted + accumulated
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=used,
        title={'text': title},
        gauge={
            'axis': {'range': [0, max_value]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, contracted], 'color': "lightgray"},
                {'range': [contracted, max_value], 'color': "orange"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': contracted
            }
        }))

    # Atualizar layout para lidar com valores que excedem o limite
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=50, b=20),
        annotations=[
            dict(
                x=0.5, y=0.55, xref='paper', yref='paper',
                text="Valor atual",
                showarrow=False
            ),
            dict(
                x=0.5, y= 0, xref='paper', yref='paper',  # Ajuste x e y conforme necessário
                text=f"Acumulado: {accumulated}",
                showarrow=False,
                font=dict(color="gray", size=12)
            )
        ]
    )

    return fig

def debug_display_data(cliente_id=None, start_date=None, end_date=None):
    logging.info("Executando debug_display_data...")
    try:
        if cliente_id:
            clients = session.query(Client).filter_by(id=cliente_id).all()
        else:
            clients = session.query(Client).all()

        debug_data = []
        table_data = []  # Para armazenar os dados da tabela de debug
        for client in clients:
            entregas_creative = session.query(DeliveryControl).filter(
                DeliveryControl.client_id == client.id,
                DeliveryControl.job_creation_date >= start_date,
                DeliveryControl.job_creation_date <= end_date
            ).all()

            mandalecas_usadas_criacao = sum(entrega.used_creative_mandalecas for entrega in entregas_creative if identificar_categoria(entrega.job_title, entrega.project) == "Criação")
            mandalecas_usadas_adaptacao = sum(entrega.used_creative_mandalecas for entrega in entregas_creative if identificar_categoria(entrega.job_title, entrega.project) == "Adaptação")

            # Log para verificar mandalecas usadas
            logging.info(f"Cliente: {client.name}, Mandalecas usadas (Criação): {mandalecas_usadas_criacao}, Entregas: {[(entrega.job_title, entrega.used_creative_mandalecas) for entrega in entregas_creative]}")
            logging.info(f"Cliente: {client.name}, Mandalecas usadas (Adaptação): {mandalecas_usadas_adaptacao}, Entregas: {[(entrega.job_title, entrega.used_creative_mandalecas) for entrega in entregas_creative]}")

            mandalecas_acumuladas_criacao = client.accumulated_creative_mandalecas if client.accumulated_creative_mandalecas else 0
            mandalecas_acumuladas_adaptacao = client.accumulated_format_adaptation_mandalecas if client.accumulated_format_adaptation_mandalecas else 0

            debug_data.append({
                'Nome do Cliente': client.name,
                'Total de Mandalecas Usadas (Criação)': mandalecas_usadas_criacao,
                'Mandalecas Contratadas (Criação)': client.n_monthly_contracted_creative_mandalecas,
                'Mandalecas Acumuladas (Criação)': mandalecas_acumuladas_criacao,
                'Total de Mandalecas Usadas (Adaptação)': mandalecas_usadas_adaptacao,
                'Mandalecas Contratadas (Adaptação)': client.n_monthly_contracted_format_adaptation_mandalecas,
                'Mandalecas Acumuladas (Adaptação)': mandalecas_acumuladas_adaptacao
            })

            # Log dos dados de cada cliente
            logging.info(f"Dados do cliente {client.name}: {debug_data[-1]}")

            # Adicionar dados para a tabela de debug
            for entrega in entregas_creative:
                table_data.append({
                    'Cliente': client.name,
                    'used_creative_mandalecas': entrega.used_creative_mandalecas,
                    'job_creation_date': entrega.job_creation_date
                })

        for data in debug_data:
            col1, col2 = st.columns(2)
            with col1:
                fig_criacao = display_gauge_chart(
                    "Criação",
                    data['Mandalecas Contratadas (Criação)'],
                    data['Mandalecas Acumuladas (Criação)'],
                    data['Total de Mandalecas Usadas (Criação)']
                )
                st.plotly_chart(fig_criacao)
            with col2:
                fig_adaptacao = display_gauge_chart(
                    "Adaptação",
                    data['Mandalecas Contratadas (Adaptação)'],
                    data['Mandalecas Acumuladas (Adaptação)'],
                    data['Total de Mandalecas Usadas (Adaptação)']
                )
                st.plotly_chart(fig_adaptacao)

        # Exibir tabela de debug
        if table_data:
            df_table = pd.DataFrame(table_data)
            st.write("Tabela de Debug:")
            st.dataframe(df_table)

            # Log dos dados da tabela de debug
            logging.info(f"Tabela de Debug: {df_table.to_dict(orient='records')}")

    except Exception as e:
        logging.error(f"Erro ao exibir os dados: {e}", exc_info=True)
        st.write(f"Erro ao exibir os dados: {e}")

def page_criacao(cliente_selecionado=None):
    st.title("Controle de entregas: Criação")

    # Carregar os clientes disponíveis
    clientes = session.query(Client).all()
    cliente_nomes = [cliente.name for cliente in clientes]

    # Obter a data de hoje e o primeiro dia do mês atual
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)

    # Seleção do cliente e intervalo de datas
    col1, col2, col3 = st.columns(3)
    with col1:
        cliente_selecionado = st.selectbox("Selecione o Cliente", cliente_nomes, index=cliente_nomes.index(cliente_selecionado) if cliente_selecionado else 0)
    with col2:
        data_inicio = st.date_input("Data de início", value=first_day_of_month, key="data_inicio_criacao_page")
    with col3:
        data_fim = st.date_input("Data de fim", value=today, key="data_fim_criacao_page")

    cliente = session.query(Client).filter_by(name=cliente_selecionado).first()
    if cliente:
        # Exibir dados completos para depuração relacionados ao cliente selecionado
        debug_display_data(cliente_id=cliente.id, start_date=data_inicio, end_date=data_fim)

        # Tabela de informações de entrega contratual
        entregas = session.query(DeliveryControl).filter(
            DeliveryControl.client_id == cliente.id,
            DeliveryControl.job_creation_date >= data_inicio,
            DeliveryControl.job_creation_date <= data_fim
        ).all()

        if entregas:
            tabela_dados = [{
                "Título do Job": entrega.job_title,
                "Data de Início do Job": entrega.job_creation_date,
                "Número de Mandalecas": extract_mandalecas(entrega.job_title),
                "Link do job": entrega.job_link,
                "Categoria": entrega.category
            } for entrega in entregas]

            df_tabela = pd.DataFrame(tabela_dados)
            st.write("Informações de entrega contratual:")
            st.dataframe(df_tabela)
        else:
            st.write("Nenhum dado encontrado para o período selecionado.")

        # Botão para atualizar dados
        uploaded_file = st.file_uploader("Envie o arquivo .xlsx de exportação de Jobs do Operand", type="xlsx")
        if uploaded_file:
            # Processar o arquivo .xlsx usando a nova função
            process_xlsx_file(uploaded_file)
