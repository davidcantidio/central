# import streamlit as st
# from plotly.graph_objects import Figure
# from common.models import JobCategoryEnum
# from page_entregas.utils.gauge import display_gauge_chart


# # Função para exibir o gráfico de Criação
# def display_creation_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
#     st.write("**Criação**")
    
#     # Container estilizado para o gráfico gauge
#     with st.container():
#         # Obter dados de mandalecas contratadas, usadas e acumuladas para criação
#         contracted = mandalecas_contratadas.get(JobCategoryEnum.CRIACAO, 0)
#         used = mandalecas_usadas.get(JobCategoryEnum.CRIACAO, 0)
#         accumulated = mandalecas_acumuladas.get(JobCategoryEnum.CRIACAO, 0)

#         # Gerar o gráfico gauge de criação usando a função utilitária
#         gauge_chart = display_gauge_chart(
#             title="Criação",
#             contracted=contracted,
#             used=used,
#             accumulated=accumulated
#         )

#         # Exibir o gráfico
#         st.plotly_chart(gauge_chart, use_container_width=True)
