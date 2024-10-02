import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import pandas as pd
from sqlalchemy.orm import Session
from common.models import AttentionPoints  # Verifique se o caminho está correto
import logging
from page_entregas.attention_points.attention_points_modal import edit_modal, delete_modal, add_attention_point_modal


def display_attention_points_table(cliente_id, data_inicio, data_fim, engine):
    """
    Exibe a tabela de pontos de atenção para um cliente, em um intervalo de datas,
    com botões de Editar e Excluir, encapsulada em um container estilizado.
    """
    try:
        with Session(bind=engine) as session:
            attention_points = session.query(AttentionPoints).filter(
                AttentionPoints.client_id == cliente_id,
                AttentionPoints.date.between(data_inicio, data_fim)
            ).order_by(AttentionPoints.date.desc()).all()

        if not attention_points:
            st.info("Nenhum ponto de atenção encontrado para o período selecionado.")
        else:
            data = []
            for ap in attention_points:
                data.append({
                    'Data': ap.date.strftime('%d %b. %Y'),
                    'Ponto de Atenção': ap.attention_point,
                    'ID': ap.id
                })

            attention_points_df = pd.DataFrame(data)

            # Definir o CSS para o container apenas da tabela
            css_tabela = """
            {
                border: 1px dashed lightgray;
                border-radius: 10px;
                padding: 15px;
                margin-top: 10px;
                background-color: white;
            }
            """

            # Encapsular a tabela e os botões de ação no container estilizado
            with stylable_container(
                key="tabela_attention_points",
                css_styles=css_tabela
            ):
                st.write("**Pontos de Atenção**")
                # Exibir a tabela com botões de ação
                for index, row in attention_points_df.iterrows():
                    col1, col2, col3, col4 = st.columns([2, 7, 1, 1])
                    col1.write(row['Data'])
                    col2.write(row['Ponto de Atenção'])
                    if col3.button('✏️', key=f'edit_{row["ID"]}', help='Editar'):
                        st.session_state['edit_item_id'] = row['ID']
                        st.session_state['edit_modal_open'] = True  # Abrir modal de edição
                    if col4.button('🗑️', key=f'delete_{row["ID"]}', help='Excluir'):
                        st.session_state['delete_item_id'] = row['ID']
                        st.session_state['delete_modal_open'] = True  # Abrir modal de exclusão
                add_attention_point_modal(engine)

        # Processar edição - abrir o modal ao clicar no botão de editar
        if st.session_state.get('edit_modal_open'):
            edit_modal(engine, st.session_state['edit_item_id'])

        # Processar exclusão - abrir o modal ao clicar no botão de excluir
        if st.session_state.get('delete_modal_open'):
            delete_modal(engine, st.session_state['delete_item_id'])

    except Exception as e:
        st.error(f"Erro ao carregar pontos de atenção: {e}")
        logging.error(f"Erro ao carregar pontos de atenção: {e}")
    
