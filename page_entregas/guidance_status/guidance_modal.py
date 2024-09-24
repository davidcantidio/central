# import streamlit as st
# from datetime import datetime
# from streamlit_modal import Modal
# from common.models import RedesSociaisGuidance
# from page_entregas.utils.assessoria_plan_utils import salvar_data_envio, determinar_status
# import logging



# # Função para exibir o modal de envio do direcionamento
# def display_guidance_modal(cliente_id):
#     # Inicializa o modal com título
#     modal = Modal("Data de Envio do Direcionamento", key="enviar-direcionamento-modal", max_width=800)

#     # Verifica se o modal foi solicitado (se o botão foi clicado)
#     if st.button("Enviar Direcionamento"):
#         logging.info(f"Usuário clicou no botão 'Enviar Direcionamento' para o cliente ID {cliente_id}")
#         modal.open()

#     # Verifica se o modal está aberto
#     if modal.is_open():
#         logging.info(f"Modal 'Data de Envio do Direcionamento' foi aberto para o cliente ID {cliente_id}")
        
#         # Conteúdo do modal
#         with modal.container():
#             # Input para seleção da data de envio
#             selected_date = st.date_input("Selecione a Data de Envio", value=datetime.today())
            
#             # Botão para confirmar a data selecionada
#             if st.button("Confirmar"):
#                 logging.info(f"Tentando salvar a data de envio do direcionamento para o cliente ID {cliente_id}")
                
#                 # Salvar a data de envio no banco de dados
#                 salvar_data_envio(cliente_id, selected_date, RedesSociaisGuidance, determinar_status)
                
#                 # Atualiza a sessão com a nova data
#                 st.session_state['guidance_send_date'] = selected_date
#                 modal.close()  # Fecha o modal
#                 st.success("Data de envio do direcionamento atualizada com sucesso!")
#                 st.rerun()  # Recarrega a página para refletir as mudanças
