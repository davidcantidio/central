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


def adjust_mandaleca_usage(engine, cliente_id, adjustment, data_inicio, data_fim, delivery_category):
    from common.models import DeliveryControl

    with Session(bind=engine) as session:
        # Usar a data de início do período selecionado para ajustar as mandalecas
        target_date = data_inicio

        delivery = session.query(DeliveryControl).filter(
            DeliveryControl.client_id == cliente_id,
            DeliveryControl.delivery_category == delivery_category,
            DeliveryControl.job_creation_date == target_date  # Usando o atributo correto
        ).first()

        if adjustment > 0:
            if not delivery:
                delivery = DeliveryControl(
                    client_id=cliente_id,
                    delivery_category=delivery_category,
                    used_mandalecas=adjustment,
                    job_creation_date=target_date  # Usando o atributo correto
                )
                session.add(delivery)
            else:
                delivery.used_mandalecas += adjustment
        elif adjustment < 0:
            if delivery and delivery.used_mandalecas + adjustment >= 0:
                delivery.used_mandalecas += adjustment
                if delivery.used_mandalecas == 0:
                    session.delete(delivery)
            else:
                st.warning("Não é possível ter mandalecas usadas negativas.")

        session.commit()
