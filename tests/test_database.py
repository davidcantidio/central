import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from models.database import Base, init_db  # Ajuste o caminho conforme necessário

@pytest.fixture(scope="module")
def test_engine():
    """Cria uma engine de teste para um banco de dados em memória."""
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope="module")
def test_session(test_engine):
    """Cria uma sessão de teste a partir da engine de teste."""
    Base.metadata.create_all(test_engine)
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session  # disponibiliza a sessão para o teste
    session.close()

@pytest.fixture(scope="module")
def prepare_database(test_engine):
    """Prepara o banco de dados para testes, criando todas as tabelas."""
    Base.metadata.create_all(test_engine)
    yield  # Aqui não precisamos de pós-processamento, mas poderia ser usado para limpeza.
    Base.metadata.drop_all(test_engine)

def test_init_db(test_session, prepare_database):
    # Supondo que você tenha uma classe/model chamado 'User' ou similar
    # Verifique se é possível criar uma instância e adicionar à sessão
    # Isso serve como um teste simples para verificar se a tabela existe
    from models.models import Users  # Ajuste o caminho do import conforme necessário
    user_instance = Users(email='test@example.com', password='abc123', first_name='Test', last_name='User')
    test_session.add(user_instance)
    test_session.commit()

    # Verifique se a instância foi realmente adicionada
    added_user = test_session.query(Users).filter_by(email='test@example.com').first()
    assert added_user is not None
    assert added_user.first_name == 'Test'
