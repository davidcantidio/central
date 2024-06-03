import re
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from common.models import DeliveryControlCreative, Client, Users, CategoryEnum
from common.database import engine
from sqlalchemy.dialects.postgresql import JSON
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

# Função para identificar a categoria do trabalho
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

# Função para converter valores para data
def convert_to_date(value):
    if pd.isna(value):
        return None
    return value.date() if isinstance(value, pd.Timestamp) else value

# Função para calcular e atualizar mandalecas acumuladas
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
    
@st.experimental_dialog("Correspondência de clientes", width="large")
def match_client_dialog():
    if not st.session_state.get("unmatched_clients"):
        return

    # Verificações e prints de depuração
    st.write(f"Clientes não correspondidos antes da ação: {st.session_state.unmatched_clients}")
    st.write(f"Clientes a serem adicionados: {st.session_state.clients_to_add}")

    index, client_name = st.session_state.unmatched_clients[0]
    st.write(f"Nome do cliente na planilha: {client_name}")

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
                # Se o cliente selecionado não estiver no banco de dados, ele deve estar na lista de novos clientes
                selected_client = next((client for client in st.session_state.clients_to_add if client['name'] == selected_client_name), None)
            if selected_client:
                if not isinstance(selected_client, dict):
                    # Cliente existente no banco de dados
                    if not selected_client.aliases:
                        selected_client.aliases = []
                    selected_client.aliases.append(client_name)
                else:
                    # Cliente na fila para ser adicionado
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
            st.write(f"Clientes não correspondidos após a adição: {st.session_state.unmatched_clients}")
            st.write(f"Clientes a serem adicionados após a adição: {st.session_state.clients_to_add}")
            st.rerun()

    if st.button("Ignorar", key=f"ignore_button_{index}"):
        st.write(f"Antes de ignorar: {st.session_state.unmatched_clients}")  # Mensagem de depuração antes de remover o cliente
        st.session_state.unmatched_clients.pop(0)
        st.write(f"Depois de ignorar: {st.session_state.unmatched_clients}")  # Mensagem de depuração após remover o cliente
        st.session_state.actions_taken.append(("ignorado", client_name))
        st.rerun()

    if st.button("Voltar", key=f"back_button_{index}"):
        if st.session_state.actions_taken:
            last_action, client_data = st.session_state.actions_taken.pop()
            if last_action in ["correspondido", "ignorado"]:
                st.session_state.unmatched_clients.insert(0, (index, client_data))
            elif last_action == "adicionado":
                st.session_state.unmatched_clients.insert(0, (index, client_data))
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

        # Exibir os dados carregados para depuração
        st.write("Dados carregados da planilha:")
        st.dataframe(df)

        # Listas para armazenar valores não encontrados
        unmatched_clients = []
        client_name_map = {}

        # Processar os dados para encontrar valores não correspondidos
        for index, row in df.iterrows():
            client_name = row['Cliente']
            client = session.query(Client).filter((Client.name == client_name) | (Client.aliases.contains([client_name]))).first()
            if not client:
                unmatched_clients.append((index, client_name))
            else:
                client_name_map[index] = client

        # Armazenar clientes não encontrados no estado da sessão
        st.session_state.unmatched_clients = unmatched_clients
        st.session_state.client_name_map = client_name_map
        st.session_state.clients_to_add = []
        st.session_state.actions_taken = []

        # Exibir a caixa de diálogo para o primeiro cliente não encontrado
        if unmatched_clients:
            match_client_dialog()

        # Processar os dados e inseri-los no banco de dados
        for index, row in df.iterrows():
            if index in client_name_map:
                client = client_name_map[index]
                user_in_charge = session.query(Users).filter_by(first_name=row['Responsável']).first()
                requested_by = session.query(Users).filter_by(first_name=row['Requisitante']).first()

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
                        requested_by_id=row['Requisitante'],
                        category=categoria,
                        project=row['Projeto']
                    )
                    session.add(new_entry)
        session.commit()
        st.success("Dados processados e inseridos com sucesso!")

        # Atualizar os valores acumulados de mandalecas
        for client in set(client_name_map.values()):
            calcular_e_atualizar_mandalecas_acumuladas(client)

        # Exibir os dados atualizados do banco de dados
        updated_data = session.query(DeliveryControlCreative).filter(
            DeliveryControlCreative.client_id.in_([client.id for client in set(client_name_map.values())])).all()
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
uploaded_file = st.file_uploader("Carregue o arquivo Excel", type=["xlsx"])
if uploaded_file:
    process_xlsx_file(uploaded_file)

# Botão para concluir e salvar todas as mudanças no banco de dados
if st.button("Concluir"):
    for client_data in st.session_state.clients_to_add:
        new_client = Client(
            name=client_data.name,
            n_monthly_contracted_creative_mandalecas=client_data.n_monthly_contracted_creative_mandalecas,
            n_monthly_contracted_format_adaptation_mandalecas=client_data.n_monthly_contracted_format_adaptation_mandalecas,
            n_monthly_contracted_content_production_mandalecas=client_data.n_monthly_contracted_content_mandalecas,
            aliases=client_data.aliases
        )
        session.add(new_client)
    session.commit()
    st.success("Todos os clientes adicionados com sucesso!")
