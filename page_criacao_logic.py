import re
import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, Client, Users
from common.database import engine
import plotly.graph_objects as go
from datetime import datetime
from process_xlsx import process_xlsx_file, identificar_categoria, extract_mandalecas
import matplotlib.pyplot as plt

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()

def display_gauge_chart(title, contracted, used):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=used,
        title={'text': title},
        gauge={'axis': {'range': [0, contracted]},
               'bar': {'color': "green"},
               'steps': [{'range': [0, contracted], 'color': "lightgray"}]}))

    fig.update_layout(height=250)  # Ajuste a altura conforme necessário

    st.plotly_chart(fig)

def debug_display_data(cliente_id=None, start_date=None, end_date=None):
    try:
        if cliente_id:
            clients = session.query(Client).filter_by(id=cliente_id).all()
        else:
            clients = session.query(Client).all()

        debug_data = []
        for client in clients:
            entregas = session.query(DeliveryControlCreative).filter(
                DeliveryControlCreative.client_id == client.id,
                DeliveryControlCreative.job_creation_date >= start_date,
                DeliveryControlCreative.job_creation_date <= end_date
            ).all()

            mandalecas_usadas_criacao = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Criação")
            mandalecas_usadas_adaptacao = sum(entrega.used_adaptacao_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Adaptação")
            mandalecas_usadas_conteudo = sum(entrega.used_conteudo_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Conteúdo")

            mandalecas_acumuladas_criacao = client.accumulated_creative_mandalecas if client.accumulated_creative_mandalecas else 0
            mandalecas_acumuladas_adaptacao = client.accumulated_format_adaptation_mandalecas if client.accumulated_format_adaptation_mandalecas else 0
            mandalecas_acumuladas_conteudo = client.accumulated_content_mandalecas if client.accumulated_content_mandalecas else 0

            debug_data.append({
                'Nome do Cliente': client.name,
                'Total de Mandalecas Usadas (Criação)': mandalecas_usadas_criacao,
                'Total de Mandalecas Usadas (Adaptação)': mandalecas_usadas_adaptacao,
                'Total de Mandalecas Usadas (Conteúdo)': mandalecas_usadas_conteudo,
                'Mandalecas Contratadas (Criação)': client.n_monthly_contracted_creative_mandalecas,
                'Mandalecas Contratadas (Adaptação)': client.n_monthly_contracted_format_adaptation_mandalecas,
                'Mandalecas Contratadas (Conteúdo)': client.n_monthly_contracted_content_production_mandalecas,
                'Mandalecas Acumuladas (Criação)': mandalecas_acumuladas_criacao,
                'Mandalecas Acumuladas (Adaptação)': mandalecas_acumuladas_adaptacao,
                'Mandalecas Acumuladas (Conteúdo)': mandalecas_acumuladas_conteudo
            })

        for data in debug_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                display_gauge_chart(
                    "Criação",
                    data['Mandalecas Contratadas (Criação)'],
                    data['Total de Mandalecas Usadas (Criação)']
                )
            with col2:
                display_gauge_chart(
                    "Conteúdo",
                    data['Mandalecas Contratadas (Conteúdo)'],
                    data['Total de Mandalecas Usadas (Conteúdo)']
                )
            with col3:
                display_gauge_chart(
                    "Adaptação",
                    data['Mandalecas Contratadas (Adaptação)'],
                    data['Total de Mandalecas Usadas (Adaptação)']
                )

    except Exception as e:
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
        entregas = session.query(DeliveryControlCreative).filter(
            DeliveryControlCreative.client_id == cliente.id,
            DeliveryControlCreative.job_creation_date >= data_inicio,
            DeliveryControlCreative.job_creation_date <= data_fim
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
