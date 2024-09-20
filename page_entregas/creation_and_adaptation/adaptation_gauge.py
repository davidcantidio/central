import streamlit as st
from plotly.graph_objects import Figure
from common.models import JobCategoryEnum
from page_entregas.utils.gauge import display_gauge_chart


# Função para exibir o gráfico de Adaptação
def display_adaptation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
    st.write("**Adaptação de Formato**")
    
    # Container estilizado para o gráfico gauge
    with st.container():
        # Obter dados de mandalecas contratadas, usadas e acumuladas para adaptação de formato
        contracted = mandalecas_contratadas.get(JobCategoryEnum.ADAPTACAO, 0)
        used = mandalecas_usadas.get(JobCategoryEnum.ADAPTACAO, 0)
        accumulated = mandalecas_acumuladas.get(JobCategoryEnum.ADAPTACAO, 0)

        # Gerar o gráfico gauge de adaptação usando a função utilitária
        gauge_chart = display_gauge_chart(
            title="Adaptação de Formato",
            contracted=contracted,
            used=used,
            accumulated=accumulated
        )

        # Exibir o gráfico
        st.plotly_chart(gauge_chart, use_container_width=True)
