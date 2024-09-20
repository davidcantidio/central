import streamlit as st
from plotly.graph_objects import Figure
from streamlit_extras.stylable_container import stylable_container
from page_entregas.utils.gauge import display_gauge_chart

# ===========================================================
# Funções para Exibição do Gauge de Texto de Blog
# ===========================================================

def display_blog_text_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    """
    Exibe o gauge (gráfico de medidor) de uso de mandalecas para texto de blog.
    """
    st.write("**Texto de Blog**")

    with stylable_container(key="blog_text_gauge", 
                            css_styles="""
                            {
                                border: 1px solid #d3d3d3;
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 45px;
                            }
                            """):
        # Exibir o gráfico de gauge para o texto de blog
        gauge_chart = display_gauge_chart(
            title="Texto de Blog",
            contracted=mandalecas_contratadas.get('BlogText', 0),
            used=mandalecas_usadas.get('BlogText', 0),
            accumulated=mandalecas_acumuladas.get('BlogText', 0)
        )
        st.plotly_chart(gauge_chart)

