# import streamlit as st
# from page_entregas.utils.gauge import display_gauge_chart
# from common.models import JobCategoryEnum

# # Função para exibir os gráficos de gauge de tráfego pago
# def display_traffic_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
#     st.write("**Tráfego Pago**")
    
#     with st.container():
#         # Criar colunas internas para os gráficos de tráfego pago
#         col1, col2 = st.columns(2)

#         # Gauge para Tráfego Pago Estático
#         with col1:
#             gauge_chart_static = display_gauge_chart(
#                 title="Tráfego Pago (Estático)",
#                 contracted=mandalecas_contratadas.get(JobCategoryEnum.STATIC_TRAFEGO_PAGO, 0),
#                 used=mandalecas_usadas.get(JobCategoryEnum.STATIC_TRAFEGO_PAGO, 0),
#                 accumulated=mandalecas_acumuladas.get(JobCategoryEnum.STATIC_TRAFEGO_PAGO, 0)
#             )
#             st.plotly_chart(gauge_chart_static, use_container_width=True)

#         # Gauge para Tráfego Pago Animado
#         with col2:
#             gauge_chart_animated = display_gauge_chart(
#                 title="Tráfego Pago (Animado)",
#                 contracted=mandalecas_contratadas.get(JobCategoryEnum.ANIMATED_TRAFEGO_PAGO, 0),
#                 used=mandalecas_usadas.get(JobCategoryEnum.ANIMATED_TRAFEGO_PAGO, 0),
#                 accumulated=mandalecas_acumuladas.get(JobCategoryEnum.ANIMATED_TRAFEGO_PAGO, 0)
#             )
#             st.plotly_chart(gauge_chart_animated, use_container_width=True)
