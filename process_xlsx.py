import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, DeliveryControlRedesSociais, Client, Users, CategoryEnumCreative, CategoryEnumRedesSociais
from common.database import engine
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import streamlit as st
import uuid
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
import logging

# Configura o log
logging.basicConfig(filename='process_xlsx.log', level=logging.ERROR)

# Crie uma sessão
Session = sessionmaker(bind=engine)

# Função para extrair o número de mandalecas
def extract_mandalecas(title):
    match = re.search(r'mdl\s?(\d+[.,]?\d*)', title, re.IGNORECASE)
    if match:
        mandalecas = match.group(1).replace(',', '.')
        return float(mandalecas)
    return None

# Função para identificar a categoria do trabalho
def identificar_categoria(titulo, projeto):
    titulo_lower = str(titulo).lower()
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
def calcular_e_atualizar_mandalecas_acumuladas(client, session):
    job_mais_antigo = session.query(DeliveryControlCreative).filter_by(client_id=client.id).order_by(DeliveryControlCreative.job_creation_date).first()
    if not job_mais_antigo:
        return
    
    data_mais_antiga = job_mais_antigo.job_creation_date
    data_atual = datetime.now()
    numero_meses = relativedelta(data_atual, data_mais_antiga).years * 12 + relativedelta(data_atual, data_mais_antiga).months + 1
    
    mandalecas_contratadas_criacao = numero_meses * (client.n_monthly_contracted_creative_mandalecas or 0)
    mandalecas_contratadas_adaptacao = numero_meses * (client.n_monthly_contracted_format_adaptation_mandalecas or 0)
    mandalecas_contratadas_conteudo = numero_meses * (client.n_monthly_contracted_content_mandalecas or 0)
    mandalecas_contratadas_reels = numero_meses * (client.n_monthly_contracted_reels_mandalecas or 0)
    mandalecas_contratadas_stories = numero_meses * (client.n_monthly_contracted_stories_mandalecas or 0)
    mandalecas_contratadas_cards = numero_meses * (client.n_monthly_contracted_cards_mandalecas or 0)
    
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()
    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Criação")
    mandalecas_usadas_adaptacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Adaptação")
    mandalecas_usadas_conteudo = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Conteúdo")
    mandalecas_usadas_reels = sum ((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Reels")
    mandalecas_usadas_stories = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Stories")
    mandalecas_usadas_cards = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Cards")
    
    client.accumulated_creative_mandalecas = mandalecas_contratadas_criacao - mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_contratadas_adaptacao - mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_contratadas_conteudo - mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_contratadas_stories - mandalecas_usadas_stories
    client.accumulated_reels_mandalecas = mandalecas_contratadas_reels - mandalecas_usadas_reels
    client.accumulated_cards_mandalecas = mandalecas_contratadas_cards - mandalecas_usadas_cards
    
    session.commit()

def process_xlsx_file(uploaded_file):
    session = Session()
    try:
        df = pd.read_excel(uploaded_file)

        df['Data de criação'] = pd.to_datetime(df['Data de criação'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['Data Início'] = pd.to_datetime(df['Data Início'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['Data de Conclusão'] = pd.to_datetime(df['Data de Conclusão'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

        unmatched_clients = []
        client_name_map = {}
        unmatched_categories = []
        job_category_map = {}

        existing_clients = {client.name: client for client in session.query(Client).all()}

        for index, row in df.iterrows():
            client_name = str(row['Cliente'])
            client = existing_clients.get(client_name) or session.query(Client).filter(Client.aliases.contains([client_name])).first()
            if not client:
                unmatched_clients.append((index, client_name))
            else:
                client_name_map[index] = client

            categoria = identificar_categoria(row['Título'], row['Projeto'])
            if not categoria:
                unmatched_categories.append((index, row['Título']))
            else:
                job_category_map[index] = categoria

        # Inicializa os valores no st.session_state
        st.session_state.unmatched_clients = unmatched_clients
        st.session_state.client_name_map = client_name_map
        st.session_state.clients_to_add = []
        st.session_state.actions_taken = []

        st.session_state.unmatched_categories = unmatched_categories
        st.session_state.job_category_map = job_category_map
        st.session_state.df = df
        st.session_state.session = session

        if unmatched_categories:
            match_categories_dialog()
        else:
            process_jobs(df, client_name_map, job_category_map, session)

    except Exception as e:
        logging.error(f"Erro ao processar dados: {e}")
        st.error(f"Erro ao processar dados: {e}")

def process_jobs(df, client_name_map, job_category_map, session):
    for index, row in df.iterrows():
        if index in client_name_map:
            client = client_name_map[index]
            user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
            requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

            doc_num = str(row['Nº Doc']).split('.')[0]
            job_link = f"https://app4.operand.com.br/jobs/{doc_num}"

            mandalecas = extract_mandalecas(row['Título'])
            categoria = job_category_map.get(index)

            doc_id = int(doc_num)

            project_type = row['Projeto']

            if 'Redes Sociais' in project_type:
                existing_entry = session.query(DeliveryControlRedesSociais).filter_by(id=doc_id).first()
            else:
                existing_entry = session.query(DeliveryControlCreative).filter_by(id=doc_id).first()

            job_creation_date = convert_to_date(row['Data de criação'])
            job_start_date = convert_to_date(row['Data Início'])
            job_finish_date = convert_to_date(row['Data de Conclusão'])

            if 'Redes Sociais' in project_type:
                if existing_entry:
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
                    new_entry = DeliveryControlRedesSociais(
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
            else:
                if existing_entry:
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

    for client in set(client_name_map.values()):
        calcular_e_atualizar_mandalecas_acumuladas(client, session)

    session.close()

@st.experimental_dialog("Correspondência de clientes", width="large")
def match_client_dialog():
    if not st.session_state.get("unmatched_clients"):
        return

    index, client_name = st.session_state.unmatched_clients[0]

    # Combine os clientes existentes no banco de dados com os que estão na fila para serem adicionados
    session = st.session_state.session
    existing_clients = [client.name for client in session.query(Client).all()]
    new_clients = [client['name'] for client in st.session_state.clients_to_add]
    all_clients = existing_clients + new_clients

    action = st.radio(
        "Ação:",
        ("Corresponder a um cliente existente", "Adicionar como novo cliente"),
        key=f"action_{index}"
    )

    if action == "Corresponder a um cliente existente":
        selected_client_name = st.selectbox(
            "Selecione o cliente correspondente:",
            all_clients,
            key=f"client_{index}"
        )
        if st.button("Confirmar Correspondência", key=f"confirm_match_{index}"):
            selected_client = session.query(Client).filter_by(name=selected_client_name).first()
            if not selected_client:
                selected_client = next((client for client in st.session_state.clients_to_add if client['name'] == selected_client_name), None)
            if selected_client:
                if not isinstance(selected_client, dict):
                    if not selected_client.aliases:
                        selected_client.aliases = []
                    selected_client.aliases.append(client_name)
                else:
                    if 'aliases' not in selected_client:
                        selected_client['aliases'] = []
                    selected_client['aliases'].append(client_name)
                st.session_state.client_name_map[index] = selected_client
                st.session_state.unmatched_clients.pop(0)
                st.session_state.actions_taken.append("correspondido")
                st.experimental_rerun()

    elif action == "Adicionar como novo cliente":
        new_client_name = st.text_input("Nome do cliente", value=client_name)
        creative_mandalecas = st.number_input("Mandalecas mensais contratadas (Criação)", min_value=0)
        adaptation_mandalecas = st.number_input("Mandalecas mensais contratadas (Adaptação)", min_value=0)
        content_mandalecas = st.number_input("Mandalecas mensais contratadas (Conteúdo)", min_value=0)
        if st.button("Confirmar Adição", key=f"confirm_add_{index}"):
            new_client = {
                'name': new_client_name,
                'creative_mandalecas': creative_mandalecas,
                'adaptation_mandalecas': adaptation_mandalecas,
                'content_mandalecas': content_mandalecas,
                'aliases': [client_name]
            }
            st.session_state.clients_to_add.append(new_client)
            st.session_state.client_name_map[index] = new_client
            st.session_state.unmatched_clients.pop(0)
            st.session_state.actions_taken.append("adicionado")
            st.experimental_rerun()

    if st.button("Ignorar", key=f"ignore_button_{index}"):
        st.session_state.unmatched_clients.pop(0)
        st.session_state.actions_taken.append("ignorado")
        st.experimental_rerun()

    if st.button("Voltar", key=f"back_button_{index}"):
        if st.session_state.actions_taken:
            last_action = st.session_state.actions_taken.pop()
            if last_action in ["correspondido", "ignorado"]:
                st.session_state.unmatched_clients.insert(0, (index, client_name))
            elif last_action == "adicionado":
                st.session_state.unmatched_clients.insert(0, (index, client_name))
                st.session_state.clients_to_add.pop()
            st.experimental_rerun()


@st.experimental_dialog("Correspondência de categorias", width="large")
def match_categories_dialog():
    if not st.session_state.get("unmatched_categories"):
        return

    st.write("Correspondência de categorias para trabalhos pendentes:")

    updated_categories = {}
    for index, job_title in st.session_state.unmatched_categories:
        st.write(f"Título do Job: {job_title}")
        categoria_escolhida = st.selectbox(
            f"Escolha a categoria para o job '{job_title}':",
            [category.value for category in CategoryEnumCreative] + [category.value for category in CategoryEnumRedesSociais],
            key=f"categoria_{index}"
        )
        updated_categories[index] = categoria_escolhida

    if st.button("Confirmar Todas"):
        st.session_state.unmatched_categories = []
        st.session_state.job_category_map.update(updated_categories)
        process_jobs(st.session_state.df, st.session_state.client_name_map, st.session_state.job_category_map, st.session_state.session)
        st.experimental_rerun()

# Código para carregar o arquivo e processá-lo
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"], key="file_uploader_1")
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.session_state.df = df
    process_xlsx_file(uploaded_file)

if st.button("Concluir"):
    session = Session()
    try:
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
    except Exception as e:
        logging.error(f"Erro ao adicionar novos clientes: {e}")
        st.error(f"Erro ao adicionar novos clientes: {e}")
    finally:
        session.close()
