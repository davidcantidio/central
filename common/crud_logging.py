from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

# Configuração básica do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_or_create(session: Session, model, defaults=None, **kwargs):
    """
    Obtém ou cria uma instância de um modelo.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = {k: v for k, v in kwargs.items()}
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True
