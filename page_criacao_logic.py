import re
import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, Client, Users
from common.database import engine
import plotly.graph_objects as go
from datetime import datetime, date

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()

# Função para extrair o número de mandalecas
def extract_mandalecas(title):
    match = re.search(r'mdl\s?(\d+[.,]?\d*)', title, re.IGNORECASE)
    if match:
        mandalecas = match.group(1).replace(',', '.')
        return float(mandalecas)
    return None

def identificar_categoria(titulo, projeto):
    titulo_lower = titulo.lower()
    projeto_lower = projeto.lower()
    
    if "produção de conteúdo" in titulo_lower:
        return "conteudo"
    elif "adaptação" in titulo_lower:
        return "adaptacao"
    elif "redes" not in projeto_lower and "sociais" not in projeto_lower:
        return "criacao"
    else:
        return None

def display_gauge_charts(client_name, criacao, adaptacao, conteudo, max_criacao, max_adaptacao, max_conteudo):
    col1, col2, col3 = st.columns(3)

    with col1:
        fig_criacao = go.Figure(go.Indicator(
            mode="gauge+number",
            value=criacao,
            title={'text': f"Criação: {client_name}", 'font': {'size': 12}},
            gauge={'axis': {'range': [0, max_criacao]},
                   'bar': {'color': "green"},
                   'steps': [
                       {'range': [0, criacao], 'color': "lightgreen"},
                       {'range': [criacao, max_criacao], 'color': "lightgray"}],
                   'threshold': {
                       'line': {'color': "red", 'width': 4},
                       'thickness': 0.75,
                       'value': max_criacao}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        fig_criacao.update_layout(height=200, width=200, margin={'t': 20, 'b': 20, 'l': 20, 'r': 20})
        st.plotly_chart(fig_criacao, use_container_width=True)

    with col2:
        fig_adaptacao = go.Figure(go.Indicator(
            mode="gauge+number",
            value=adaptacao,
            title={'text': f"Adaptação: {client_name}", 'font': {'size': 12}},
            gauge={'axis': {'range': [0, max_adaptacao]},
                   'bar': {'color': "blue"},
                   'steps': [
                       {'range': [0, adaptacao], 'color': "lightblue"},
                       {'range': [adaptacao, max_adaptacao], 'color': "lightgray"}],
                   'threshold': {
                       'line': {'color': "red", 'width': 4},
                       'thickness': 0.75,
                       'value': max_adaptacao}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        fig_adaptacao.update_layout(height=200, width=200, margin={'t': 20, 'b': 20, 'l': 20, 'r': 20})
        st.plotly_chart(fig_adaptacao, use_container_width=True)

    with col3:
        fig_conteudo = go.Figure(go.Indicator(
            mode="gauge+number",
            value=conteudo,
            title={'text': f"Conteúdo: {client_name}", 'font': {'size': 12}},
            gauge={'axis': {'range': [0, max_conteudo]},
                   'bar': {'color': "red"},
                   'steps': [
                       {'range': [0, conteudo], 'color': "pink"},
                       {'range': [conteudo, max_conteudo], 'color': "lightgray"}],
                   'threshold': {
                       'line': {'color': "red", 'width': 4},
                       'thickness': 0.75,
                       'value': max_conteudo}},
            domain={'x': [0, 1], 'y': [0, 1]}
        ))
        fig_conteudo.update_layout(height=200, width=200, margin={'t': 20, 'b': 20, 'l': 20, 'r': 20})
        st.plotly_chart(fig_conteudo, use_container_width=True)

def display_delivery_table(client_id):
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=client_id).all()
    
    if entregas:
        tabela_dados = [{
            "Título do Job": entrega.job_title,
            "Data de Início do Job": entrega.job_start_date,
            "Data de Criação": entrega.job_creation_date,
            "Data de Conclusão": entrega.job_finish_date,
            "Número de Mandalecas": entrega.used_creative_mandalecas,
            "Status": entrega.job_status,
            "Responsável": entrega.user_in_charge.first_name if entrega.user_in_charge else "N/A",
            "Requisitante": entrega.requested_by.first_name if entrega.requested_by else "N/A",
            "Categoria": entrega.category,
            "Projeto": entrega.project
        } for entrega in entregas]
        
        df_tabela = pd.DataFrame(tabela_dados)
        st.write("Informações de entrega contratual:")
        st.dataframe(df_tabela)
    else:
        st.write("Nenhum dado encontrado para o cliente selecionado.")

def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

def calcular_e_atualizar_mandalecas_acumuladas(cliente):
    # Obtém todas as entregas do cliente
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=cliente.id).all()

    # Inicializa as mandalecas acumuladas
    mandalecas_acumuladas_criacao = 0
    mandalecas_acumuladas_adaptacao = 0
    mandalecas_acumuladas_conteudo = 0

    # Dicionários para armazenar o uso de mandalecas por mês
    uso_mensal_criacao = {}
    uso_mensal_adaptacao = {}
    uso_mensal_conteudo = {}

    # Calcula o uso de mandalecas por mês
    for entrega in entregas:
        categoria = identificar_categoria(entrega.job_title, entrega.job_title)
        mes_ano = (entrega.job_creation_date.year, entrega.job_creation_date.month)

        if categoria == "criacao":
            if mes_ano not in uso_mensal_criacao:
                uso_mensal_criacao[mes_ano] = 0
            uso_mensal_criacao[mes_ano] += entrega.used_creative_mandalecas
        elif categoria == "adaptacao":
            if mes_ano not in uso_mensal_adaptacao:
                uso_mensal_adaptacao[mes_ano] = 0
            uso_mensal_adaptacao[mes_ano] += entrega.used_creative_mandalecas
        elif categoria == "conteudo":
            if mes_ano not in uso_mensal_conteudo:
                uso_mensal_conteudo[mes_ano] = 0
            uso_mensal_conteudo[mes_ano] += entrega.used_creative_mandalecas

    # Calcula as mandalecas acumuladas
    for (ano, mes), usado in uso_mensal_criacao.items():
        contratado = cliente.n_monthly_contracted_creative_mandalecas
        if usado < contratado:
            mandalecas_acumuladas_criacao += (contratado - usado)

    for (ano, mes), usado in uso_mensal_adaptacao.items():
        contratado = cliente.n_monthly_contracted_format_adaptation_mandalecas
        if usado < contratado:
            mandalecas_acumuladas_adaptacao += (contratado - usado)

    for (ano, mes), usado in uso_mensal_conteudo.items():
        contratado = cliente.n_monthly_contracted_content_mandalecas
        if usado < contratado:
            mandalecas_acumuladas_conteudo += (contratado - usado)

    # Atualiza os campos de mandalecas acumuladas no banco de dados
    cliente.accumulated_creative_mandalecas = mandalecas_acumuladas_criacao
    cliente.accumulated_format_adaptation_mandalecas = mandalecas_acumuladas_adaptacao
    cliente.accumulated_content_mandalecas = mandalecas_acumuladas_conteudo
    session.commit()
def debug_display_data(cliente_id=None):
    st.write("Executando debug_display_data...")
    try:
        if cliente_id:
            clients = session.query(Client).filter_by(id=cliente_id).all()
        else:
            clients = session.query(Client).all()
        
        debug_data = []
        for client in clients:
            entregas = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()
            
            mandalecas_usadas_criacao = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "criacao")
            mandalecas_usadas_adaptacao = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "adaptacao")
            mandalecas_usadas_conteudo = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "conteudo")
            
            mandalecas_acumuladas_criacao = client.accumulated_creative_mandalecas if client.accumulated_creative_mandalecas else 0
            mandalecas_acumuladas_adaptacao = client.accumulated_format_adaptation_mandalecas if client.accumulated_format_adaptation_mandalecas else 0
            mandalecas_acumuladas_conteudo = client.accumulated_content_mandalecas if client.accumulated_content_mandalecas else 0

            max_criacao = client.n_monthly_contracted_creative_mandalecas + mandalecas_acumuladas_criacao
            max_adaptacao = client.n_monthly_contracted_format_adaptation_mandalecas + mandalecas_acumuladas_adaptacao
            max_conteudo = client.n_monthly_contracted_content_mandalecas + mandalecas_acumuladas_conteudo
            
        
            display_gauge_charts(
                client.name,
                mandalecas_usadas_criacao,
                mandalecas_usadas_adaptacao,
                mandalecas_usadas_conteudo,
                max_criacao,
                max_adaptacao,
                max_conteudo
            )

            # Chamar a função para exibir a tabela de entregas
            display_delivery_table(client.id)

        df_debug = pd.DataFrame(debug_data)
        st.write("Dados completos dos clientes e suas mandalecas (antes de aplicar os filtros):")
        st.dataframe(df_debug)
    except Exception as e:
        st.write(f"Erro ao exibir os dados: {e}")

def page_criacao(cliente_selecionado=None):
    st.title("Controle de entregas: Criação")

    # Carregar os clientes disponíveis
    clientes = session.query(Client).all()
    cliente_nomes = [cliente.name for cliente in clientes]

    # Seleção do cliente e intervalo de datas
    col1, col2, col3 = st.columns(3)
    with col1:
        cliente_selecionado = st.selectbox("Selecione o Cliente", cliente_nomes, index=cliente_nomes.index(cliente_selecionado) if cliente_selecionado else 0)
    with col2:
        data_inicio = st.date_input("Data de início", value=datetime.now().date(), key="data_inicio_criacao")
    with col3:
        data_fim = st.date_input("Data de fim", value=datetime.now().date(), key="data_fim_criacao")

    cliente = session.query(Client).filter_by(name=cliente_selecionado).first()
    if cliente:
        st.write(f"Cliente selecionado: {cliente.name}")

        # Exibir dados completos para depuração relacionados ao cliente selecionado
        debug_display_data(cliente_id=cliente.id)

        # Tabela de informações de entrega contratual
        entregas = session.query(DeliveryControlCreative).filter(
            DeliveryControlCreative.client_id == cliente.id,
            DeliveryControlCreative.job_start_date >= data_inicio,
            DeliveryControlCreative.job_start_date <= data_fim
        ).all()

        if entregas:
            tabela_dados = [{
                "Nome do Cliente": entrega.client.name,
                "Título do Job": entrega.job_title,
                "Data de Início do Job": entrega.job_start_date,
                "Número de Mandalecas": entrega.used_creative_mandalecas
            } for entrega in entregas]

            df_tabela = pd.DataFrame(tabela_dados)
            st.write("Informações de entrega contratual:")
            st.dataframe(df_tabela)
        else:
            st.write("Nenhum dado encontrado para o período selecionado.")

        # Botão para atualizar dados
        uploaded_file = st.file_uploader("Envie o arquivo .xlsx de exportação de Jobs do Operand", type="xlsx")
        if uploaded_file:
            # Ler o arquivo .xlsx em um DataFrame
            df = pd.read_excel(uploaded_file)

            # Convertendo colunas de data para o formato correto
            df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%d-%m-%Y')
            df['Data Início'] = pd.to_datetime(df['Data Início'], format='%d-%m-%Y')
            df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%d-%m-%Y')

            # Listas para armazenar valores não encontrados
            unmatched_clients = []
            unmatched_users_in_charge = []
            unmatched_requested_by = []

            # Processar os dados para encontrar valores não correspondidos
            for _, row in df.iterrows():
                client = session.query(Client).filter_by(name=row['Cliente']).first()
                user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
                requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

                if not client:
                    unmatched_clients.append(row['Cliente'])
                if not user_in_charge:
                    unmatched_users_in_charge.append(row['Responsável'])
                if not requested_by:
                    unmatched_requested_by.append(row['Requisitante'])

            if unmatched_clients:
                st.warning(f"Clientes não encontrados no banco de dados: {set(unmatched_clients)}")
            if unmatched_users_in_charge:
                st.warning(f"Responsáveis não encontrados no banco de dados: {set(unmatched_users_in_charge)}")
            if unmatched_requested_by:
                st.warning(f"Requisitantes não encontrados no banco de dados: {set(unmatched_requested_by)}")

            if st.button("Processar Dados"):
                try:
                    for _, row in df.iterrows():
                        client = session.query(Client).filter_by(name=row['Cliente']).first()
                        user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
                        requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

                        if client and user_in_charge and requested_by:
                            project_url = row.get('URL do projeto', '')

                            # Extração do valor de mandalecas
                            mandalecas = extract_mandalecas(row['Título'])
                            categoria = identificar_categoria(row['Título'], row['Projeto'])

                            # Processar o campo "Nº Doc"
                            doc_num = str(row['Nº Doc']).replace('.', '')
                            doc_id = int(doc_num)

                            existing_entry = session.query(DeliveryControlCreative).filter_by(id=doc_id).first()

                            job_creation_date = convert_to_date(row['Data de criação'])
                            job_start_date = convert_to_date(row['Data Início'])
                            job_finish_date = convert_to_date(row['Data de Conclusão'])

                            if existing_entry:
                                # Atualizar a entrada existente
                                existing_entry.client_id = client.id
                                existing_entry.job_link = project_url
                                existing_entry.job_title = row['Título']
                                existing_entry.used_creative_mandalecas = mandalecas
                                existing_entry.job_creation_date = job_creation_date
                                existing_entry.job_start_date = job_start_date
                                existing_entry.job_finish_date = job_finish_date
                                existing_entry.job_status = row['Status']
                                existing_entry.user_in_charge_id = user_in_charge.id
                                existing_entry.requested_by_id = requested_by.id
                                existing_entry.category = categoria
                                existing_entry.project = row['Projeto']
                            else:
                                # Criar uma nova entrada
                                new_entry = DeliveryControlCreative(
                                    id=doc_id,
                                    client_id=client.id,
                                    job_link=project_url,
                                    job_title=row['Título'],
                                    used_creative_mandalecas=mandalecas,
                                    job_creation_date=job_creation_date,
                                    job_start_date=job_start_date,
                                    job_finish_date=job_finish_date,
                                    job_status=row['Status'],
                                    user_in_charge_id=user_in_charge.id,
                                    requested_by_id=requested_by.id,
                                    category=categoria,
                                    project=row['Projeto']
                                )
                                session.add(new_entry)
                    session.commit()
                    st.success("Dados processados e inseridos com sucesso!")

                    # Atualizar os valores acumulados de mandalecas
                    calcular_e_atualizar_mandalecas_acumuladas(cliente)

                    # Exibir os dados atualizados do banco de dados
                    updated_data = session.query(DeliveryControlCreative).all()
                    updated_df = pd.DataFrame([{
                        'Cliente': entry.client.name,
                        'Título': entry.job_title,
                        'Mandalecas': entry.used_creative_mandalecas,
                        'Status': entry.job_status,
                        'Data de criação': entry.job_creation_date,
                        'Data Início': entry.job_start_date,
                        'Data de Conclusão': entry.job_finish_date,
                        'Responsável': entry.user_in_charge.first_name,
                        'Requisitante': entry.requested_by.first_name,
                        'Categoria': entry.category,
                        'Projeto': entry.project
                    } for entry in updated_data])
                    st.write("Dados atualizados no banco de dados:")
                    st.dataframe(updated_df)

                    # Visualização dos dados com gráficos do tipo gauge
                    for client in session.query(Client).all():
                        deliveries = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()
                        if deliveries:
                            total_creative_used = sum(float(d.used_creative_mandalecas) for d in deliveries)
                            accumulated_creative_mandalecas = client.accumulated_creative_mandalecas if client.accumulated_creative_mandalecas else 0
                            accumulated_creative_mandalecas += total_creative_used

                            display_gauge_charts(
                                f"Creative Mandalecas de {client.name}",
                                client.n_monthly_contracted_creative_mandalecas,
                                accumulated_creative_mandalecas
                            )

                except Exception as e:
                    st.error(f"Erro ao processar dados: {e}")

def main():
    st.set_page_config(page_title="Mandala Dashboard", layout="wide")

    menu = st.selectbox("Menu", ["Clientes", "Tráfego Pago", "Assessoria", "Criação", "Redes Sociais"])

    if menu == "Criação":
        page_criacao()

if __name__ == "__main__":
    main()
