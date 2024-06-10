import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, Client, Users, CategoryEnum
from common.database import engine
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import streamlit as st
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func

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

# Função para identificar a categoria do trabalho
def identificar_categoria(titulo, projeto):
    titulo_lower = titulo.lower()
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

    if len(categorias_encontradas) == 1:
        return categorias_encontradas.pop()
    else:
        return None

# Função para converter valores para data
def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

# Função para calcular e atualizar mandalecas acumuladas
def calcular_e_atualizar_mandalecas_acumuladas(client):
    # Identificar o job mais antigo
    job_mais_antigo = session.query(DeliveryControlCreative).filter_by(client_id=client.id).order_by(DeliveryControlCreative.data_criacao).first()
    
    if not job_mais_antigo:
        return  # Nenhum job encontrado, nada a fazer
    
    data_mais_antiga = job_mais_antigo.data_criacao
    data_atual = datetime.now()
    
    # Calcular o número de meses entre o mês do job mais antigo e o mês atual
    numero_meses = relativedelta(data_atual, data_mais_antiga).years * 12 + relativedelta(data_atual, data_mais_antiga).months + 1  # +1 para incluir o mês atual
    
    # Calcular mandalecas contratadas acumuladas
    mandalecas_contratadas_criacao = numero_meses * (client.n_monthly_contracted_creative_mandalecas or 0)
    mandalecas_contratadas_adaptacao = numero_meses * (client.n_monthly_contracted_format_adaptation_mandalecas or 0)
    mandalecas_contratadas_conteudo = numero_meses * (client.n_monthly_contracted_content_mandalecas or 0)
    mandalecas_contratadas_reels = numero_meses * (client.n_monthly_contracted_reels_mandalecas or 0)
    mandalecas_contratadas_stories = numero_meses * (client.n_monthly_contracted_stories_mandalecas or 0)
    mandalecas_contratadas_cards = numero_meses * (client.n_monthly_contracted_cards_mandalecas or 0)
    
    # Somar mandalecas usadas desde o job mais antigo
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()
    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Criação")
    mandalecas_usadas_adaptacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Adaptação")
    mandalecas_usadas_conteudo = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Conteúdo")
    mandalecas_usadas_reels = sum ((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Reels")
    mandalecas_usadas_stories = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Stories")
    mandalecas_usadas_cards = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Cards")
    
    # Calcular mandalecas acumuladas
    client.accumulated_creative_mandalecas = mandalecas_contratadas_criacao - mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_contratadas_adaptacao - mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_contratadas_conteudo - mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_contratadas_stories - mandalecas_usadas_stories
    client.accumulated_reels_mandalecas = mandalecas_contratadas_reels - mandalecas_usadas_reels
    client.accumulated_cards_mandalecas = mandalecas_contratadas_cards - mandalecas_usadas_cards
    
    # Salvar mudanças no banco de dados
    session.commit()

def process_xlsx_file(uploaded_file):
    try:
        # Ler o arquivo .xlsx em um DataFrame
        df = pd.read_excel(uploaded_file)

        # Convertendo colunas de data para o formato correto
        df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

        # Listas para armazenar valores não encontrados
        unmatched_clients = []
        client_name_map = {}
        unmatched_categories = []
        job_category_map = {}

        # Processar os dados para encontrar valores não correspondidos
        for index, row in df.iterrows():
            client_name = row['Cliente']
            client = session.query(Client).filter((Client.name == client_name) | (Client.aliases.contains([client_name]))).first()
            if not client:
                unmatched_clients.append((index, client_name))
            else:
                client_name_map[index] = client

            # Processar a categoria do trabalho
            categoria = identificar_categoria(row['Título'], row['Projeto'])
            if not categoria:
                unmatched_categories.append((index, row['Título']))
            else:
                job_category_map[index] = categoria

        # Armazenar clientes e categorias não encontrados no estado da sessão
        st.session_state.unmatched_clients = unmatched_clients
        st.session_state.client_name_map = client_name_map
        st.session_state.clients_to_add = []
        st.session_state.actions_taken = []

        st.session_state.unmatched_categories = unmatched_categories
        st.session_state.job_category_map = job_category_map

        # Exibir a caixa de diálogo para correspondência de categorias
        if unmatched_categories:
            match_categories_dialog()

        # Processar os dados e inseri-los no banco de dados
        for index, row in df.iterrows():
            if index in client_name_map:
                client = client_name_map[index]
                user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
                requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

                # Construir o job_link
                doc_num = str(row['Nº Doc']).split('.')[0]  # Obter o número do documento antes do primeiro ponto
                job_link = f"https://app4.operand.com.br/jobs/{doc_num}"

                # Extração do valor de mandalecas
                mandalecas = extract_mandalecas(row['Título'])
                categoria = job_category_map.get(index)  # Usar categoria do mapa ou None

                # Processar o campo "Nº Doc"
                doc_id = int(doc_num)

                existing_entry = session.query(DeliveryControlCreative).filter_by(id=doc_id).first()

                job_creation_date = convert_to_date(row['Data de criação'])
                job_start_date = convert_to_date(row['Data Início'])
                job_finish_date = convert_to_date(row['Data de Conclusão'])

                if existing_entry:
                    # Atualizar a entrada existente
                    existing_entry.client_id = client.id
                    existing_entry.job_link = job_link
                    existing_entry.job_title = row['Título']
                    existing_entry.used_mandalecas = mandalecas
                    existing_entry.job_creation_date = job_creation_date
                    existing_entry.job_start_date = job_start_date
                    existing_entry.job_finish_date = job_finish_date
                    existing_entry.job_status = row['Status']
                    existing_entry.user_in_charge_id = user_in_charge.id if user_in_charge else None
                    existing_entry.requested_by_id = requested_by.id if requested_by else None
                    existing_entry.category = categoria
                    existing_entry.project = row['Projeto']
                else:
                    # Criar uma nova entrada
                    new_entry = DeliveryControlCreative(
                        id=doc_id,
                        client_id=client.id,
                        job_link=job_link,
                        job_title=row['Título'],
                        used_mandalecas=mandalecas,
                        job_creation_date=job_creation_date,
                        job_start_date=job_start_date,
                        job_finish_date=job_finish_date,
                        job_status=row['Status'],
                        user_in_charge_id=user_in_charge.id if user_in_charge else None,
                        requested_by_id=requested_by.id if requested_by else None,
                        category=categoria,
                        project=row['Projeto']
                    )
                    session.add(new_entry)
        session.commit()
        st.success("Dados processados e inseridos com sucesso!")

        # Atualizar os valores acumulados de mandalecas
        for client in set(client_name_map.values()):
            calcular_e_atualizar_mandalecas_acumuladas(client)

    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")

@st.experimental_dialog("Correspondência de categorias", width="large")
def match_categories_dialog():
    if not st.session_state.get("unmatched_categories"):
        return

    st.write("Correspondência de categorias para trabalhos pendentes:")

    for index, job_title in st.session_state.unmatched_categories:
        st.write(f"Título do Job: {job_title}")
        categoria_escolhida = st.selectbox(
            f"Escolha a categoria para o job '{job_title}':",
            [category.value for category in CategoryEnum],
            key=f"categoria_{index}_{uuid.uuid4()}"
        )
        st.session_state.job_category_map[index] = categoria_escolhida

    if st.button("Confirmar Todas"):
        st.session_state.unmatched_categories = []
        st.rerun()

# Código para carregar o arquivo e processá-lo
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])
if uploaded_file:
    process_xlsx_file(uploaded_file)

if st.button("Concluir"):
    for client_data in st.session_state.clients_to_add:
        new_client = Client(
            name=client_data['name'],
            n_monthly_contracted_creative_mandalecas=client_data['creative_mandalecas'],
            n_monthly_contracted_format_adaptation_mandalecas=client_data['adaptation_mandalecas'],
            n_monthly_contracted_content_production_mandalecas=client_data['content_mandalecas'],
            aliases=client_data['aliases']
        )
        session.add(new_client)
    session.commit()
    st.success("Todos os clientes adicionados com sucesso!")

