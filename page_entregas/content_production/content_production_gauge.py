import streamlit as st
from plotly.graph_objects import Figure
from streamlit_extras.stylable_container import stylable_container
from page_entregas.utils.gauge import display_gauge_chart

# ===========================================================
# Funções para Exibição do Gauge de Produção de Conteúdo
# ===========================================================

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
        # Exibir o gráfico de gauge para produção de conteúdo
        gauge_chart = display_gauge_chart(
            title="Produção de Conteúdo",
            contracted=mandalecas_contratadas.get('ContentProduction', 0),
            used=mandalecas_usadas.get('ContentProduction', 0),
            accumulated=mandalecas_acumuladas.get('ContentProduction', 0)
        )
        st.plotly_chart(gauge_chart)
