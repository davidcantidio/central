import streamlit as st
from streamlit_modal import Modal
from sqlalchemy.orm import Session
import logging
from common.models import AttentionPoints
from datetime import datetime

def edit_modal(engine, item_id):
    # Criar e configurar o modal
    modal = Modal("Editar Ponto de Atenção", key=f'edit_modal_{item_id}', padding=20, max_width=744)

    # Exibir modal se o botão de edição foi clicado
    if st.session_state['edit_modal_open']:
        with Session(bind=engine) as session:
            attention_point = session.query(AttentionPoints).get(item_id)

            if attention_point is None:
                st.error("Ponto de atenção não encontrado.")
                st.session_state['edit_modal_open'] = False  # Fechar o modal
                return

            # Exibir o conteúdo do modal
            with modal.container():
                st.write("### Editar Ponto de Atenção")

                # Exibir o formulário para edição
                with st.form(key=f'edit_form_{item_id}'):
                    selected_date = st.date_input("Selecione a Data do Ponto de Atenção", value=attention_point.date)
                    attention_description = st.text_area("Descrição do Ponto de Atenção", value=attention_point.attention_point)
                    submit_edit = st.form_submit_button(label='Salvar Alterações')

                    # Processar a edição após a submissão
                    if submit_edit:
                        if attention_description:
                            try:
                                attention_point.date = selected_date
                                attention_point.attention_point = attention_description
                                session.commit()  # Commit da alteração
                                st.success("Ponto de atenção atualizado com sucesso!")
                                st.session_state['edit_item_id'] = None  # Resetar o estado após a edição
                                st.session_state['edit_modal_open'] = False  # Fechar modal
                                st.rerun()  # Recarregar a página para refletir a edição
                            except Exception as e:
                                st.error(f"Erro ao atualizar o ponto de atenção: {e}")
                        else:
                            st.error("A descrição do ponto de atenção não pode estar vazia.")

def delete_modal(engine, item_id):
    """
    Exibe o modal de confirmação de exclusão do ponto de atenção.
    """
    modal = Modal("Excluir Ponto de Atenção", key=f'delete_modal_{item_id}', padding=20, max_width=744)

    # Abrir o modal se o botão de exclusão foi clicado
    if st.session_state['delete_modal_open']:
        with Session(bind=engine) as session:
            attention_point = session.query(AttentionPoints).get(item_id)

            if attention_point is None:
                st.error("Ponto de atenção não encontrado.")
                st.session_state['delete_modal_open'] = False  # Fechar o modal se o item não for encontrado
                return

            # Exibir o conteúdo do modal
            with modal.container():
                st.write("### Excluir Ponto de Atenção")
                st.warning(f"Tem certeza que deseja excluir o ponto de atenção do dia {attention_point.date.strftime('%d %b. %Y')}? Esta ação não pode ser desfeita.")

                # Botões de confirmação e cancelamento
                col1, col2 = st.columns(2)
                with col1:
                    confirm_delete = st.button("Excluir", key=f'confirm_delete_{item_id}')
                with col2:
                    cancel_delete = st.button("Cancelar", key=f'cancel_delete_{item_id}')

                # Processar exclusão
                if confirm_delete:
                    try:
                        session.delete(attention_point)  # Deletar o ponto
                        session.commit()  # Commit da exclusão
                        st.success("Ponto de atenção excluído com sucesso!")
                        st.session_state['delete_item_id'] = None  # Resetar o estado após exclusão
                        st.session_state['delete_modal_open'] = False  # Fechar o modal
                        st.rerun()  # Recarregar a página
                    except Exception as e:
                        st.error(f"Erro ao excluir o ponto de atenção: {e}")
                elif cancel_delete:
                    st.info("Operação de exclusão cancelada.")
                    st.session_state['delete_modal_open'] = False  # Fechar o modal se o usuário cancelar

# Função para adicionar um novo ponto de atenção utilizando streamlit-modal
def add_attention_point_modal(engine):
    # Passo 3: Definir o modal
    modal = Modal("Adicionar Novo Ponto de Atenção", key="adicionar_ponto_modal", padding=20, max_width=744)

    # Passo 4: Botão para abrir o modal
    if st.button("Adicionar Ponto de Atenção"):
        modal.open()

    # Passo 5: Exibir o modal se estiver aberto
    if modal.is_open():
        with modal.container():
            st.write("### Novo Ponto de Atenção")
            # Passo 6: Exibir o formulário dentro do modal
            with st.form(key='new_attention_point_form'):
                selected_date = st.date_input("Selecione a Data do Ponto de Atenção", value=datetime.today())
                attention_description = st.text_area("Descrição do Ponto de Atenção")
                submit_new = st.form_submit_button(label='Salvar')

                # Manipulação da submissão
                if submit_new:
                    if attention_description:  # Verifica se a descrição não está vazia
                        save_new_attention_point(st.session_state["cliente_id"], selected_date, attention_description, engine)
                        st.success("Ponto de atenção adicionado com sucesso!")
                        modal.close()  # Fechar o modal
                        st.rerun()  # Recarregar a página
                    else:
                        st.error("A descrição do ponto de atenção não pode estar vazia.")

# Função para salvar o novo ponto de atenção no banco de dados
def save_new_attention_point(cliente_id, attention_date, attention_point, engine):
    try:
        with Session(bind=engine) as session:
            new_entry = AttentionPoints(
                client_id=cliente_id,
                date=attention_date,
                attention_point=attention_point
            )
            session.add(new_entry)
            session.commit()  # Commit da nova entrada
            st.success("Ponto de atenção salvo com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar o ponto de atenção: {e}")
