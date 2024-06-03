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
    entregas = session.query(DeliveryControlCreative).filter_by(client_id=client.id).all()

    mandalecas_usadas_criacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Criação")
    mandalecas_usadas_adaptacao = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Adaptação")
    mandalecas_usadas_conteudo = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Conteúdo")
    mandalecas_usadas_reels = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Reels")
    mandalecas_usadas_stories = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Stories")
    mandalecas_usadas_cards = sum((entrega.used_creative_mandalecas or 0) for entrega in entregas if identificar_categoria(entrega.job_title, entrega.project) == "Cards")

    client.accumulated_creative_mandalecas = mandalecas_usadas_criacao
    client.accumulated_format_adaptation_mandalecas = mandalecas_usadas_adaptacao
    client.accumulated_content_mandalecas = mandalecas_usadas_conteudo
    client.accumulated_stories_mandalecas = mandalecas_usadas_stories
    client.accumulated_reels_mandalecas = mandalecas_usadas_reels
    client.accumulated_cards_mandalecas = mandalecas_usadas_cards

    session.commit()

@st.experimental_dialog("Correspondência de categorias", width="large")
def match_category_dialog():
    if not st.session_state.get("unmatched_categories"):
        return

    # Obter o índice e o título do trabalho do primeiro item na lista
    index, job_title = st.session_state.unmatched_categories[0]

    # Exibir o título do trabalho para o qual a categoria está sendo selecionada
    st.write(f"Título do Job: {job_title}")

    # Exibir uma caixa de seleção para escolher a categoria
    categoria_escolhida = st.selectbox(
        "Escolha a categoria:",
        [category.value for category in CategoryEnum],
        key=f"categoria_{index}_{uuid.uuid4()}"
    )

    # Botão para confirmar a correspondência
    if st.button("Fazer Correspondência", key=f"confirm_category_{index}"):
        # Armazenar a categoria escolhida no mapa de categorias
        st.session_state.job_category_map[index] = categoria_escolhida
        # Remover o item da lista de categorias não correspondidas
        st.session_state.unmatched_categories.pop(0)
        # Verificações de depuração
        st.write(f"Categoria escolhida: {categoria_escolhida}")
        st.write(f"Categorias não correspondidas restantes: {st.session_state.unmatched_categories}")
        st.write(f"Mapa de categorias: {st.session_state.job_category_map}")
        # Reiniciar o diálogo para o próximo item
        st.rerun()
st.experimental_dialog("Correspondência de clientes", width="large")
def match_client_dialog():
    if not st.session_state.get("unmatched_clients"):
        return

    index, client_name = st.session_state.unmatched_clients[0]

    # Combine os clientes existentes no banco de dados com os que estão na fila para serem adicionados
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
                st.rerun()

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
            st.rerun()

    if st.button("Ignorar", key=f"ignore_button_{index}"):
        st.session_state.unmatched_clients.pop(0)
        st.session_state.actions_taken.append("ignorado")
        st.rerun()

    if st.button("Voltar", key=f"back_button_{index}"):
        if st.session_state.actions_taken:
            last_action = st.session_state.actions_taken.pop()
            if last_action in ["correspondido", "ignorado"]:
                st.session_state.unmatched_clients.insert(0, (index, client_name))
            elif last_action == "adicionado":
                st.session_state.unmatched_clients.insert(0, (index, client_name))
                st.session_state.clients_to_add.pop()
            st.rerun()

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

        # Exibir a caixa de diálogo para o primeiro cliente não encontrado
        if unmatched_clients:
            match_client_dialog()
        elif unmatched_categories:
            match_category_dialog()

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
                    existing_entry.used_creative_mandalecas = mandalecas
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
                        used_creative_mandalecas=mandalecas,
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
