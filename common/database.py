# database.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()

# Ajuste o caminho para apontar para o diretório common
current_folder = Path(__file__).resolve().parent.parent / 'common'
PATH_TO_DB = current_folder / 'db_mandala.sqlite'

engine = create_engine(f'sqlite:///{PATH_TO_DB}')

def init_db():
    Base.metadata.create_all(bind=engine)
