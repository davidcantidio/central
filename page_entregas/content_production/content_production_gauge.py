import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from page_entregas.utils.gauge import display_gauge_chart
from common.models import DeliveryCategoryEnum

def display_content_production_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    """
    Exibe o gauge (gráfico de medidor) para produção de conteúdo.
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

        # Exibir o gráfico de gauge
        display_gauge_chart(
            title="Produção de Conteúdo",
            contracted=contracted,
            used=used,
            accumulated=accumulated
        )
