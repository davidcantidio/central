import streamlit as st
from streamlit_modal import Modal
from sqlalchemy.orm import Session
import logging
from common.models import ContentProduction
from datetime import datetime

def edit_content_production_meeting_modal(engine, item_id, modal):
    if modal.is_open():
        with Session(bind=engine) as session:
            content_production = session.query(ContentProduction).get(item_id)

            if content_production is None:
                st.error("Reunião de Produção de Conteúdo não encontrada.")
                modal.close()
                return

            # Exibir o conteúdo do modal
            with modal.container():
                st.write("### Editar Reunião de Produção de Conteúdo")

                # Exibir o formulário dentro do modal
                with st.form(key=f'edit_form_{item_id}'):
                    selected_date = st.date_input("Selecione a Data da Reunião", value=content_production.date)
                    subject = st.text_area("Tema da Reunião", value=content_production.subject)
                    meeting_notes = st.text_area("Notas", value=content_production.notes)
                    submit_edit = st.form_submit_button(label='Salvar Alterações')

                    if submit_edit:
                        if subject:
                            try:
                                content_production.date = selected_date
                                content_production.subject = subject
                                content_production.notes = meeting_notes
                                session.commit()
                                st.success("Reunião atualizada com sucesso!")
                                modal.close()  # Fechar o modal
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar a Reunião de Produção de Conteúdo: {e}")
                                logging.error(f"Erro ao atualizar reunião de produção de conteúdo: {e}")
                        else:
                            st.error("A descrição da reunião não pode estar vazia.")
    else:
        modal.close()

def delete_content_production_meeting_modal(engine, item_id, modal):
    if modal.is_open():
        with Session(bind=engine) as session:
            content_production = session.query(ContentProduction).get(item_id)

            if content_production is None:
                st.error("Reunião não encontrada.")
                modal.close()
                return

            # Exibir o conteúdo do modal
            with modal.container():
                st.write("### Excluir Reunião de Produção de Conteúdo")
                st.warning(f"Tem certeza que deseja excluir a Reunião de Produção de Conteúdo do dia {content_production.date.strftime('%d %b. %Y')}? Esta ação não pode ser desfeita.")

                # Botões de confirmação e cancelamento
                col1, col2 = st.columns(2)
                with col1:
                    confirm_delete = st.button("Excluir", key=f'confirm_delete_meeting{item_id}')
                with col2:
                    cancel_delete = st.button("Cancelar", key=f'cancel_delete_meeting{item_id}')

                if confirm_delete:
                    try:
                        session.delete(content_production)
                        session.commit()
                        st.success("Reunião excluída com sucesso!")
                        modal.close()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir a Reunião de Produção de Conteúdo: {e}")
                        logging.error(f"Erro ao excluir a Reunião de Produção de Conteúdo: {e}")
                elif cancel_delete:
                    modal.close()
                    st.rerun()
    else:
        modal.close()

def add_content_production_meeting_modal(engine):
    # Inicializa o modal para adicionar Reunião de Produção de Conteúdo
    modal = Modal("Adicionar Nova Reunião de Produção de Conteúdo", key="adicionar_reunião_conteudo", padding=20, max_width=744)

    # Botão para abrir o modal
    if st.button("Adicionar Reunião de Conteúdo"):
        modal.open()

    # Exibir o modal se estiver aberto
    if modal.is_open():
        with modal.container():
            st.write("### Nova Reunião de Produção de Conteúdo")
            with st.form(key='new_content_production_form'):
                selected_date = st.date_input("Selecione a Data do Reunião de Produção de Conteúdo", value=datetime.today())
                subject = st.text_area("Assunto da Reunião de Produção de Conteúdo")
                meeting_notes = st.text_area("Notas da Reunião")
                submit_new = st.form_submit_button(label='Salvar')

                if submit_new:
                    if subject:
                        save_new_content_production_meeting(st.session_state["cliente_id"], selected_date, subject, meeting_notes, engine)
                        st.success("Reunião adicionada com sucesso!")
                        modal.close()
                        st.rerun()
                    else:
                        st.error("A descrição da Reunião de Produção de Conteúdo não pode estar vazia.")
