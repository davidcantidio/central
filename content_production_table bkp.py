import streamlit as st
from sqlalchemy.orm import Session
import pandas as pd
from common.models import ContentProduction
import logging
from page_entregas.utils.styles import css_tabela
from page_entregas.content_production.content_production_table_modals import (
    edit_content_production_meeting_modal,
    delete_content_production_meeting_modal,
    add_content_production_meeting_modal
)
from streamlit_modal import Modal
from streamlit_extras.stylable_container import stylable_container

def display_content_production_table(cliente_id, data_inicio, data_fim, engine):
    """
    Exibe a tabela de reuniões de produção de conteúdo para um cliente, em um intervalo de datas,
    com botões de Editar e Excluir, encapsulada em um container estilizado.
    """
    try:
        with Session(bind=engine) as session:
            content_production = session.query(ContentProduction).filter(
                ContentProduction.client_id == cliente_id,
                ContentProduction.date.between(data_inicio, data_fim)
            ).order_by(ContentProduction.date.desc()).all()

        if not content_production:
            st.info("Nenhuma reunião de produção de conteúdo encontrada para o período selecionado.")
        else:
            data = []
            for cp in content_production:
                data.append({
                    'Data': cp.date.strftime('%d %b. %Y') if cp.date else '',
                    'Tema da Reunião': cp.subject,
                    'Notas': cp.notes if cp.notes else '-',
                    'ID': cp.id
                })

            content_production_df = pd.DataFrame(data)

            st.write("**Reuniões de Produção de Conteúdo**")

            # Inicializar os modais fora de qualquer container ou loop
            edit_modal = Modal("Editar Reunião", key="edit_modal_cp", max_width=800)
            delete_modal = Modal("Excluir Reunião", key="delete_modal_cp", max_width=800)

            # Exibir a tabela dentro do container estilizado
            with stylable_container(
                key="tabela_content_production",
                css_styles=css_tabela()
            ):
                # Adicionar linha de cabeçalho
                header_col1, header_col2, header_col3, header_col4 = st.columns([2, 7, 1, 1])
                header_col1.write("**Data**")
                header_col2.write("**Tema da Reunião**")
                header_col3.write("**Editar**")
                header_col4.write("**Excluir**")

                # Exibir os dados com botões de ação
                for index, row in content_production_df.iterrows():
                    # Definir a cor de fundo com base na paridade do índice
                    if index % 2 == 0:
                        row_bg_color = '#FFFFFF'  # Cor para linhas pares
                    else:
                        row_bg_color = '#F0F0F0'  # Cor para linhas ímpares

                    # Aplicar o estilo à linha usando stylable_container
                    with stylable_container(
                        key=f'row_{row["ID"]}_{index}',
                        css_styles=f'''
                        {{
                            'background-color': '{row_bg_color}';
                            'padding': '5px';
                            'border-radius': '5px';
                        }}
                        '''
                    ):
                        cols = st.columns([2, 7, 1, 1])
                        cols[0].write(row['Data'])
                        cols[1].write(row['Tema da Reunião'])
                        if cols[2].button('✏️', key=f'edit_{row["ID"]}_{index}', help='Editar'):
                            st.session_state['edit_item_id'] = row['ID']
                            edit_modal.open()
                        if cols[3].button('🗑️', key=f'delete_{row["ID"]}_{index}', help='Excluir'):
                            st.session_state['delete_item_id'] = row['ID']
                            delete_modal.open()

            # Chamar as funções dos modais fora do container e de qualquer loop
            if edit_modal.is_open():
                edit_content_production_meeting_modal(engine, st.session_state['edit_item_id'], edit_modal)

            if delete_modal.is_open():
                delete_content_production_meeting_modal(engine, st.session_state['delete_item_id'], delete_modal)

            # Botão para adicionar nova reunião
            add_content_production_meeting_modal(engine)

    except Exception as e:
        st.error(f"Erro ao carregar reuniões: {e}")
        logging.error(f"Erro ao carregar reuniões: {e}")

