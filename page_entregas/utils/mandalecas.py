from datetime import datetime
from common.models import DeliveryCategoryEnum, Client, DeliveryControl
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import streamlit as st  

def calcular_mandalecas(cliente: Client, data_inicio: datetime, data_fim: datetime, session: Session):
    """
    Calcula as mandalecas contratadas, usadas e acumuladas para um cliente específico.

    Parâmetros:
    - cliente (Client): Objeto do cliente.
    - data_inicio (datetime): Data de início do período.
    - data_fim (datetime): Data de fim do período.
    - session (Session): Sessão do SQLAlchemy.

    Retorna:
    - mandalecas_contratadas (dict): Mandalecas contratadas por categoria.
    - mandalecas_usadas (dict): Mandalecas usadas por categoria.
    - mandalecas_acumuladas (dict): Mandalecas acumuladas por categoria.
    """
    # Verificar se o cliente foi fornecido
    if not cliente:
        st.error("Cliente não fornecido.")
        return None, None, None

    # Mandalecas Contratadas
    mandalecas_contratadas = {
        DeliveryCategoryEnum.CONTENT_PRODUCTION: cliente.n_monthly_contracted_content_production_mandalecas or 0,
        # Adicione outras categorias conforme necessário
    }

    # Mandalecas Acumuladas
    mandalecas_acumuladas = {
        DeliveryCategoryEnum.CONTENT_PRODUCTION: cliente.accumulated_content_production_mandalecas or 0,
        # Adicione outras categorias conforme necessário
    }

    # Mandalecas Usadas no período atual
    mandalecas_usadas = {}

    # Calcular mandalecas usadas para 'Produção de Conteúdo'
    total_usadas = session.query(func.sum(DeliveryControl.used_mandalecas)).filter(
        DeliveryControl.client_id == cliente.id,
        DeliveryControl.delivery_category == DeliveryCategoryEnum.CONTENT_PRODUCTION,
        DeliveryControl.job_creation_date.between(data_inicio, data_fim)
    ).scalar() or 0

    mandalecas_usadas[DeliveryCategoryEnum.CONTENT_PRODUCTION] = total_usadas

    return mandalecas_contratadas, mandalecas_usadas, mandalecas_acumuladas
