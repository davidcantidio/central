# import streamlit as st
# from page_entregas.utils.gauge import display_gauge_chart
# from common.models import JobCategoryEnum
# from streamlit_extras.stylable_container import stylable_container
# import plotly.graph_objects as go  # Importação para criar gráficos com Plotly


# # Função para exibir o medidor do Instagram
# def display_instagram_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
#     st.write("**Instagram**")
#     with stylable_container(key="instagram_gauge", 
#                             css_styles="""
#                             {
#                                 border: 1px solid #d3d3d3;
#                                 border-radius: 10px;
#                                 padding: 15px;
#                                 margin-bottom: 45px;
#                             }
#                             """):
#         gauge_chart = display_gauge_chart(
#             title="Instagram",
#             contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_INSTAGRAM, 0),
#             used=mandalecas_usadas.get(JobCategoryEnum.FEED_INSTAGRAM, 0),
#             accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_INSTAGRAM, 0)
#         )
#         st.plotly_chart(gauge_chart)

#         # Distribuição do uso de conteúdo no Instagram
#         social_media_data = {
#             "Carrossel Instagram": mandalecas_usadas.get(JobCategoryEnum.CAROUSEL_INSTAGRAM, 0),
#             "Reels Instagram": mandalecas_usadas.get(JobCategoryEnum.REELS_INSTAGRAM, 0),
#             "Card Instagram": mandalecas_usadas.get(JobCategoryEnum.CARD_INSTAGRAM, 0)
#         }

#         pie_chart = create_pie_chart(social_media_data, "Distribuição Instagram")
#         st.plotly_chart(pie_chart)


# # Função para exibir o medidor de outras redes (LinkedIn, TikTok)
# def display_other_networks_gauge(mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas):
#     st.write("**Outras Redes**")
#     with stylable_container(key="other_networks_gauge", 
#                             css_styles="""
#                             {
#                                 border: 1px solid #d3d3d3;
#                                 border-radius: 10px;
#                                 padding: 15px;
#                                 margin-bottom: 45px;
#                             }
#                             """):
#         linkedin_gauge = display_gauge_chart(
#             title="Feed LinkedIn",
#             contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_LINKEDIN, 0),
#             used=mandalecas_usadas.get(JobCategoryEnum.FEED_LINKEDIN, 0),
#             accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_LINKEDIN, 0)
#         )
#         st.plotly_chart(linkedin_gauge)

#         tiktok_gauge = display_gauge_chart(
#             title="Feed TikTok",
#             contracted=mandalecas_contratadas.get(JobCategoryEnum.FEED_TIKTOK, 0),
#             used=mandalecas_usadas.get(JobCategoryEnum.FEED_TIKTOK, 0),
#             accumulated=mandalecas_acumuladas.get(JobCategoryEnum.FEED_TIKTOK, 0)
#         )
#         st.plotly_chart(tiktok_gauge)


# def create_pie_chart(data, title):
#     labels = list(data.keys())
#     values = list(data.values())
#     fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
#     fig.update_layout(title_text=title)
#     return fig