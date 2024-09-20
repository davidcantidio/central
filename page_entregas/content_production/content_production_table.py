import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from common.database import engine
from page_entregas.content_production.content_production_modal import modal_content_production_open
from common.models import ContentProduction

def display_content_production_table(cliente_id):
    modal = modal_content_production_open()  # Corrigida a importação do modal

    with st.container():
        st.write("**Histórico de Reuniões de Produção de Conteúdo**")
        with st.container():
            with Session(bind=engine) as session:
                content_production_data = session.query(ContentProduction).filter(ContentProduction.client_id == cliente_id).all()

                if not content_production_data:
                    content_production_df = pd.DataFrame(columns=['Data da Reunião', 'Assunto', 'Notas'])
                else:
                    content_production_df = pd.DataFrame([{
                        'Data da Reunião': row.meeting_date.strftime('%Y-%m-%d') if row.meeting_date else '',
                        'Assunto': row.meeting_subject,
                        'Notas': row.notes
                    } for row in content_production_data])

                st.table(content_production_df)

        if st.button("Adicionar Nova Reunião de Produção de Conteúdo"):
            modal.open()
