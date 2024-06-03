import streamlit as st
from sqlalchemy.orm import sessionmaker
from common.models import Client
from common.database import engine

# Crie uma sessão
Session = sessionmaker(bind=engine)
session = Session()

def match_client_dialog():
    if not st.session_state.get("unmatched_clients"):
        return

    index, client_name = st.session_state.unmatched_clients[0]
    st.write(f"Nome do cliente na planilha: {client_name}")

    action = st.radio(
        "Ação:",
        ("Corresponder a um cliente existente", "Adicionar como novo cliente"),
        key=f"action_{index}"
    )

    if action == "Corresponder a um cliente existente":
        selected_client_name = st.selectbox(
            "Selecione o cliente correspondente:",
            [client.name for client in session.query(Client).all()],
            key=f"client_{index}"
        )
        if st.button("Confirmar Correspondência", key=f"confirm_match_{index}"):
            selected_client = session.query(Client).filter_by(name=selected_client_name).first()
            if selected_client:
                if not selected_client.aliases:
                    selected_client.aliases = []
                selected_client.aliases.append(client_name)
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

def handle_unmatched_clients():
    if st.session_state.unmatched_clients:
        match_client_dialog()
