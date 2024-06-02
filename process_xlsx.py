import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, Client, Users, CategoryEnum
from common.database import engine
from datetime import datetime
import streamlit as st

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

def identificar_categoria(titulo, projeto, index):
    titulo_lower = titulo.lower()
    projeto_lower = projeto.lower()

    categorias_encontradas = set()

    if "adaptação" in titulo_lower:
        categorias_encontradas.add("Adaptação")
    if "criação" in titulo_lower:
        categorias_encontradas.add("Criação")
    if any(keyword in titulo_lower for keyword in ["story", "stories", "storie"]):
        categorias_encontradas.add("Stories")
    if any(keyword in titulo_lower for keyword in ["reel", "reels"]):
        categorias_encontradas.add("Reels")
    if any(keyword in titulo_lower for keyword in ["card", "cards"]):
        categorias_encontradas.add("Cards")

    # Se nenhuma categoria for encontrada ou mais de uma categoria for encontrada
    if not categorias_encontradas or len(categorias_encontradas) > 1:
        st.write(f"Título do Job: {titulo}")
        categoria_escolhida = st.selectbox(
            "Escolha a categoria:",
            [category.value for category in CategoryEnum],
            key=f"categoria_{index}"
        )
        return categoria_escolhida
    else:
        return categorias_encontradas.pop()

def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

def calcular_e_atualizar_mandalecas_acumuladas(client):
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()

    mandalecas_usadas_criacao = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project, entrega.id) == "Criação")
    mandalecas_usadas_adaptacao = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project, entrega.id) == "Adaptação")
    mandalecas_usadas_conteudo = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project, entrega.id) == "Conteúdo")
    mandalecas_usadas_reels = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project, entrega.id) == "Reels")
    mandalecas_usadas_stories = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project, entrega.id) == "Stories")
    mandalecas_usadas_cards = sum(entrega.used_creative_mandalecas for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project, entrega.id) == "Cards")

    client.accumulated_creative_mandalecas = mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_usadas_stories
    client.accumulated_reels_mandalecas = mandalecas_usadas_reels
    client.accumulated_cards_mandalecas = mandalecas_usadas_cards

    session.commit()

def process_xlsx_file(uploaded_file):
    try:
        # Ler o arquivo .xlsx em um DataFrame
        df = pd.read_excel(uploaded_file)

        # Convertendo colunas de data para o formato correto
        df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

        # Exibir os dados carregados para depuração
        st.write("Dados carregados da planilha:")
        st.dataframe(df)

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

        for index, row in enumerate(df.iterrows()):
            row = row[1]
            client = session.query(Client).filter_by(name=row['Cliente']).first()
            user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
            requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

            if client and user_in_charge and requested_by:
                project_url = row.get('URL do projeto', '')

                # Extração do valor de mandalecas
                mandalecas = extract_mandalecas(row['Título'])
                categoria = identificar_categoria(row['Título'], row['Projeto'], index)

                # Processar o campo "Nº Doc"
                doc_num = str(row['Nº Doc']).replace('.', '').replace(',', '')
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
        calcular_e_atualizar_mandalecas_acumuladas(client)

        # Exibir os dados atualizados do banco de dados
        updated_data = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()
        updated_df = pd.DataFrame([{
            'ID': entry.id,
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

    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")

# Use esta função para processar o arquivo carregado
if st.file_uploader("Carregue o arquivo Excel", type=["xlsx"]):
    process_xlsx_file(uploaded_file)
