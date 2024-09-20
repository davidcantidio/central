import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from common.models import Client, RedesSociaisPlan, RedesSociaisGuidance, RedesSociaisPlanStatusEnum
from common.database import engine
import streamlit as st

# Função para salvar a data de envio de um plano ou direcionamento
def salvar_data_envio(cliente_id, data_envio, model_class, status_function):
    logging.info(f"Salvando data de envio para cliente ID {cliente_id} com data {data_envio}")
    with Session(bind=engine) as session:
        try:
            if isinstance(data_envio, datetime):
                data_envio = data_envio.date()

            mes_inicio = data_envio.replace(day=1)
            logging.debug(f"Buscando registro existente para cliente ID {cliente_id} no mês {mes_inicio.strftime('%Y-%m')}")
            record = session.query(model_class).filter(
                model_class.client_id == cliente_id,
                func.strftime('%Y-%m', model_class.send_date) == mes_inicio.strftime('%Y-%m')
            ).first()

            client = session.query(Client).filter(Client.id == cliente_id).first()
            logging.debug(f"Cliente encontrado: {client}")

            # Obter o deadline_day do cliente
            if model_class == RedesSociaisPlan:
                deadline_day = client.monthly_plan_deadline_day
            elif model_class == RedesSociaisGuidance:
                deadline_day = client.monthly_redes_guidance_deadline_day
            else:
                raise ValueError("Classe de modelo desconhecida para determinação do deadline_day")

            if record:
                logging.debug(f"Registro encontrado, atualizando data de envio e status")
                record.send_date = data_envio
                record.updated_at = datetime.now()
                record.status = status_function(client, record, deadline_day)
            else:
                logging.debug(f"Nenhum registro existente encontrado, criando novo registro")
                record = model_class(
                    client_id=cliente_id,
                    send_date=data_envio,
                    updated_at=datetime.now(),
                    status=status_function(client, None, deadline_day),
                    plan_status=RedesSociaisPlanStatusEnum.AWAITING
                )
                session.add(record)

            logging.info(f"Commitando a transação no banco de dados")
            session.commit()
            st.success(f"Data de envio atualizada com sucesso.")
            st.session_state['send_date'] = data_envio

        except Exception as e:
            session.rollback()
            st.error(f"Erro ao atualizar a data de envio: {e}")
            logging.error(f"Erro ao atualizar a data de envio: {e}")

# Função para determinar o status do plano ou direcionamento
def determinar_status(cliente, record, deadline_day):
    hoje = datetime.today().date()
    prazo = datetime(hoje.year, hoje.month, deadline_day).date()
    
    if record is None or record.send_date is None:
        if hoje > prazo:
            return RedesSociaisPlanStatusEnum.DELAYED
        else:
            return RedesSociaisPlanStatusEnum.AWAITING
    else:
        send_date = record.send_date
        if isinstance(send_date, datetime):
            send_date = send_date.date()
        if send_date <= prazo:
            return RedesSociaisPlanStatusEnum.ON_TIME
        else:
            return RedesSociaisPlanStatusEnum.DELAYED

# Função utilitária para obter o range de datas do mês anterior
def get_last_month_date_range():
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_last_month = datetime(last_day_of_last_month.year, last_day_of_last_month.month, 1)
    return first_day_of_last_month, last_day_of_last_month
