import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base  # Adjust the path as necessary based on your project structure

@pytest.fixture(scope="session")
def engine():
    """
    Creates a SQLAlchemy engine instance for testing.
    This engine is connected to an in-memory SQLite database.
    It is shared across the entire test session.
    """
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="session")
def tables(engine):
    """
    Creates all tables in the database for testing, based on the SQLAlchemy Base metadata.
    It uses the 'engine' fixture to connect to the in-memory SQLite database.
    The tables are created before any tests run and dropped after all tests are completed.
    The 'yield' statement separates setup from teardown; everything before 'yield' is setup,
    and everything after is teardown.
    """
    Base.metadata.create_all(engine)
    yield  # This is where testing happens.
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine, tables):
    """
    Provides a transactional database session for testing.
    A new database session is opened for each test and rolled back at the end of the test,
    ensuring that tests remain isolated and do not interfere with each other.
    
    :param engine: The SQLAlchemy engine connected to the database, provided by the 'engine' fixture.
    :param tables: This ensures that the tables are created prior to setting up the session,
                   provided by the 'tables' fixture.
    """
    # Establish a connection and begin a transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Bind a new session to the connection
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session  # Pass the session to the test
    
    # After the test is done, roll back the transaction and close the connection
    session.close()
    connection.close()
