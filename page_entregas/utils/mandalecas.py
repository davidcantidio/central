# from datetime import datetime
# from common.models import JobCategoryEnum, DeliveryCategoryEnum, Client
# from sqlalchemy.orm import Session
# from sqlalchemy.sql import func

# # Função para calcular as mandalecas contratadas, usadas e acumuladas
# def calcular_mandalecas(cliente_id: int):
#     """
#     Função para calcular mandalecas contratadas, usadas e acumuladas para um cliente específico.
    
#     Parâmetros:
#     cliente_id (int): ID do cliente para o qual as mandalecas serão calculadas.

#     Retorna:
#     mandalecas_contratadas (dict): Mandalecas contratadas por categoria.
#     mandalecas_usadas (dict): Mandalecas usadas por categoria.
#     mandalecas_acumuladas (dict): Mandalecas acumuladas por categoria.
#     """
#     # Dicionários para armazenar as mandalecas por categoria
#     mandalecas_contratadas = {
#         JobCategoryEnum.CRIACAO: 100,   # Exemplo: valor contratado
#         JobCategoryEnum.ADAPTACAO: 50,
#         JobCategoryEnum.CONTENT_PRODUCTION: 40,
#         JobCategoryEnum.STATIC_TRAFEGO_PAGO: 30,
#         JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: 20,
#         JobCategoryEnum.FEED_INSTAGRAM: 70,
#         JobCategoryEnum.FEED_LINKEDIN: 50,
#         JobCategoryEnum.FEED_TIKTOK: 30,
#     }

#     mandalecas_usadas = {
#         JobCategoryEnum.CRIACAO: 60,    # Exemplo: valor usado
#         JobCategoryEnum.ADAPTACAO: 40,
#         JobCategoryEnum.CONTENT_PRODUCTION: 30,
#         JobCategoryEnum.STATIC_TRAFEGO_PAGO: 20,
#         JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: 10,
#         JobCategoryEnum.FEED_INSTAGRAM: 50,
#         JobCategoryEnum.FEED_LINKEDIN: 40,
#         JobCategoryEnum.FEED_TIKTOK: 20,
#     }

#     # Acumulação: diferença entre contratadas e usadas
#     mandalecas_acumuladas = {
#         categoria: mandalecas_contratadas[categoria] - mandalecas_usadas.get(categoria, 0)
#         for categoria in mandalecas_contratadas
#     }

#     return mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas

