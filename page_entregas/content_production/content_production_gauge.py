# content_production_gauge.py

import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from page_entregas.utils.gauge import display_gauge_chart
from page_entregas.utils.mandalecas import adjust_mandaleca_usage
from common.models import DeliveryCategoryEnum
from datetime import datetime

def display_content_production_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas, engine):
    """
    Exibe o gauge (gráfico de medidor) para produção de conteúdo com botões para ajustar mandalecas.
    """
    st.write("**Produção de Conteúdo**")
    
    with stylable_container(key="content_production_gauge", 
                            css_styles="""
                            {
                                border: 1px solid #d3d3d3;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 45px;
                            }
                            """):
        # Obter os valores específicos para a categoria de Produção de Conteúdo
        contracted = mandalecas_contratadas.get(DeliveryCategoryEnum.CONTENT_PRODUCTION, 0)
        used = mandalecas_usadas.get(DeliveryCategoryEnum.CONTENT_PRODUCTION, 0)
        accumulated = mandalecas_acumuladas.get(DeliveryCategoryEnum.CONTENT_PRODUCTION, 0)

        # Criar colunas para o gauge e os botões
        col1, col2 = st.columns([3, 1])

        with col1:
            # Exibir o gráfico de gauge
            display_gauge_chart(
                title="Produção de Conteúdo",
                contracted=contracted,
                used=used,
                accumulated=accumulated
            )

        with col2:
            st.write("")  # Espaçamento
            st.write("")  # Espaçamento

            # Botão para adicionar mandaleca
            if st.button("➕", key="add_mandaleca_content", help="Adicionar Mandaleca"):
                adjust_mandaleca_usage(
                    engine=engine,
                    cliente_id=st.session_state["cliente_id"],
                    adjustment=1,  # Ajuste de +1 mandaleca
                    data_inicio=st.session_state["data_inicio"],
                    data_fim=st.session_state["data_fim"],
                    delivery_category=DeliveryCategoryEnum.CONTENT_PRODUCTION
                )
                st.rerun()  # Recarrega a página para atualizar o gauge

            # Botão para remover mandaleca
            if st.button("➖", key="subtract_mandaleca_content", help="Remover Mandaleca"):
                adjust_mandaleca_usage(
                    engine=engine,
                    cliente_id=st.session_state["cliente_id"],
                    adjustment=-1,  # Ajuste de -1 mandaleca
                    data_inicio=st.session_state["data_inicio"],
                    data_fim=st.session_state["data_fim"],
                    delivery_category=DeliveryCategoryEnum.CONTENT_PRODUCTION
                )
                st.rerun()  # Recarrega a página para atualizar o gauge
