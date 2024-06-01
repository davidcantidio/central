import pytest
from models.models import * # Adjust the path as necessary based on your project structure
from sqlalchemy.exc import IntegrityError
from datetime import date

def test_create_user(db_session):
    """
    Test the creation and retrieval of a Users instance.
    Ensures that a user can be successfully added to the database and retrieved,
    with all data correctly stored.
    """
    # Creating new Department and Role instances for relation testing
    department = Department(name="IT")
    role = Role(name="Developer", friendly_name="Dev")
    db_session.add(department)
    db_session.add(role)
    db_session.commit()

    # Creating a new Users instance
    user = Users(
        password='abc123',
        addr_cep="12345678",
        addr_complement="Apartment",
        addr_neighbourhood="Downtown",
        addr_number="101",
        addr_street="Main St",
        alternative_phone="123-456-7890",
        birth_date=date(1990, 1, 1),
        cpf="12345678901",
        email="sarah@example.com",
        first_name="John",
        last_name="Doe",
        instagram="@johndoe",
        linkedin="linkedin.com/in/johndoe",
        n_jobs_contrato=10,
        price_per_job=100.00,
        profile_pic_url="http://example.com/pic.jpg",
        username="johndoe",
        whatsapp="1234567890",
        department_id=department.id,
        role_id=role.id
    )
    # Adding the new user to the database session and committing
    db_session.add(user)
    db_session.commit()

    # Retrieving the first Users instance from the database
    retrieved = db_session.query(Users).first()
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved.email == "sarah@example.com"
    assert retrieved.first_name == "John"
    assert retrieved.department.name == "IT"
    assert retrieved.role.name == "Developer"

def test_user_unique_email(db_session):
    """
    Test that the email field must be unique.
    """
    user1 = Users(email="unique@example.com", password='abc123', cpf="98765432109", first_name="Alice", last_name="Smith")
    user2 = Users(email="unique@example.com", password='abc123', cpf="12345678909", first_name="Bob", last_name="Jones")
    db_session.add(user1)
    db_session.commit()
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_repr(db_session):
    """
    Test the __repr__ method of the Users model.
    """
    user = Users(first_name="Charlie", password='abc123', last_name="Brown", email="charlie@example.com", cpf="11122233344")
    db_session.add(user)
    db_session.commit()
    assert user.__repr__() == f"<User(id={user.id}, name='{user.first_name} {user.last_name}', department='None', role='None')>"

def test_create_meta_ads_objective(db_session):
    """
    Tests the creation and retrieval of a MetaAdsObjective instance.
    This test ensures that a MetaAdsObjective can be successfully added to the database and then retrieved,
    verifying that the data remains consistent.

    :param db_session: A fixture provided by pytest that handles the SQLAlchemy session creation,
                       rollback, and teardown for each test function.
    """
    # Creating a new MetaAdsObjective instance
    objective = MetaAdsObjective(
        name="Increase Brand Awareness",
        
        friendly_name="Brand Awareness",
        description="Increase brand awareness among the target audience"
    )
    # Adding the new objective to the database session and committing the transaction
    db_session.add(objective)
    db_session.commit()
    
    # Retrieving the first MetaAdsObjective instance from the database
    retrieved = db_session.query(MetaAdsObjective).first()
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved.name == "Increase Brand Awareness"
    assert retrieved.friendly_name == "Brand Awareness"
    assert retrieved.description == "Increase brand awareness among the target audience"

def test_create_meta_ads_cta(db_session):
    """
    Tests the creation and retrieval of a MetaAdsCTA instance.
    This test ensures that a MetaAdsCTA can be successfully added to the database and then retrieved,
    verifying that the data remains consistent.

    :param db_session: A fixture provided by pytest that handles the SQLAlchemy session creation,
                       rollback, and teardown for each test function.
    """
    # Creating a new MetaAdsCTA instance
    cta = MetaAdsCTA(
        name="Learn More",
        friendly_name="Learn More",
        description="Encourage people to learn more about the product"
    )
    # Adding the new CTA to the database session and committing the transaction
    db_session.add(cta)
    db_session.commit()
    
    # Retrieving the first MetaAdsCTA instance from the database
    retrieved = db_session.query(MetaAdsCTA).first()
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved.name == "Learn More"
    assert retrieved.friendly_name == "Learn More"
    assert retrieved.description == "Encourage people to learn more about the product"

def test_create_meta_ads_objective(db_session):
    """
    Tests the creation and retrieval of a MetaAdsObjective instance.
    This test ensures that a MetaAdsObjective can be successfully added to the database and then retrieved,
    verifying that the data remains consistent.

    :param db_session: A fixture provided by pytest that handles the SQLAlchemy session creation,
                       rollback, and teardown for each test function.
    """
    # Creating a new MetaAdsObjective instance
    objective = MetaAdsObjective(
        name="Increase Brand Awareness",
        friendly_name="Brand Awareness",
        description="Increase brand awareness among the target audience"
    )
    # Adding the new objective to the database session and committing the transaction
    db_session.add(objective)
    db_session.commit()
    
    # Retrieving the first MetaAdsObjective instance from the database
    retrieved = db_session.query(MetaAdsObjective).first()
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved.name == "Increase Brand Awareness"
    assert retrieved.friendly_name == "Brand Awareness"
    assert retrieved.description == "Increase brand awareness among the target audience"

def test_create_meta_ads_cta(db_session):
    """
    Tests the creation and retrieval of a MetaAdsCTA instance.
    This test ensures that a MetaAdsCTA can be successfully added to the database and then retrieved,
    verifying that the data remains consistent.

    :param db_session: A fixture provided by pytest that handles the SQLAlchemy session creation,
                       rollback, and teardown for each test function.
    """
    # Creating a new MetaAdsCTA instance
    cta = MetaAdsCTA(
        name="Learn More",
        friendly_name="Learn More",
        description="Encourage people to learn more about the product"
    )
    # Adding the new CTA to the database session and committing the transaction
    db_session.add(cta)
    db_session.commit()
    
    # Retrieving the first MetaAdsCTA instance from the database
    retrieved = db_session.query(MetaAdsCTA).first()
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved.name == "Learn More"
    assert retrieved.friendly_name == "Learn More"
    assert retrieved.description == "Encourage people to learn more about the product"


# Teste para criar uma nova MetaAdsCTA
def test_create_meta_ads_cta(db_session):
    new_cta = MetaAdsCTA(name="Learn More", friendly_name="Learn More", description="Encourage users to learn more about the product or service")
    db_session.add(new_cta)
    db_session.commit()

    # Verifique se o novo MetaAdsCTA foi adicionado ao banco de dados
    added_cta = db_session.query(MetaAdsCTA).filter_by(name="Learn More").first()
    assert added_cta is not None
    assert added_cta.friendly_name == "Learn More"
    assert added_cta.description == "Encourage users to learn more about the product or service"

# Teste para verificar a unicidade do nome da MetaAdsCTA
def test_meta_ads_cta_name_uniqueness(db_session):
    cta1 = MetaAdsCTA(name="Subscribe", friendly_name="Subscribe", description="Get users to subscribe")
    db_session.add(cta1)
    db_session.commit()

    cta2 = MetaAdsCTA(name="Subscribe", friendly_name="Sign Up", description="Sign up for the service")
    db_session.add(cta2)
    
    # Verifica se a tentativa de adicionar uma segunda MetaAdsCTA com o mesmo nome causa uma exceção
    with pytest.raises(IntegrityError):
        db_session.commit()
    # Se uma exceção for lançada (como esperado), é bom limpar a sessão para testes subsequentes
    db_session.rollback()

# Teste para atualizar uma MetaAdsCTA
def test_update_meta_ads_cta(db_session):
    cta = MetaAdsCTA(name="Contact Us", friendly_name="Contact", description="Encourage users to contact us")
    db_session.add(cta)
    db_session.commit()

    updated_cta = db_session.query(MetaAdsCTA).filter_by(name="Contact Us").first()
    updated_cta.friendly_name = "Reach Out"
    db_session.commit()

    reloaded_cta = db_session.query(MetaAdsCTA).filter_by(name="Contact Us").first()
    assert reloaded_cta.friendly_name == "Reach Out"

# Teste para deletar uma MetaAdsCTA
def test_delete_meta_ads_cta(db_session):
    cta = MetaAdsCTA(name="Buy Now", friendly_name="Purchase", description="Encourage users to make a purchase")
    db_session.add(cta)
    db_session.commit()

    db_session.delete(cta)
    db_session.commit()

    deleted_cta = db_session.query(MetaAdsCTA).filter_by(name="Buy Now").first()
    assert deleted_cta is None
    
    # Teste para criar um novo Role
def test_create_role(db_session):
    new_role = Role(name="Analyst", friendly_name="Data Analyst")
    db_session.add(new_role)
    db_session.commit()

    # Verifique se o novo Role foi adicionado ao banco de dados
    added_role = db_session.query(Role).filter_by(name="Analyst").first()
    assert added_role is not None
    assert added_role.friendly_name == "Data Analyst"
    
    
# Teste para verificar a associação entre Role e Department
def test_role_department_association(db_session):
    department = Department(name="IT")
    db_session.add(department)
    db_session.commit()

    role = Role(name="Developer", friendly_name="Software Developer")
    role.departments.append(department)
    db_session.add(role)
    db_session.commit()

    # Verifique se o departamento está associado ao papel
    added_role = db_session.query(Role).filter_by(name="Developer").first()
    assert added_role.departments[0].name == "IT"
    
    # Teste para verificar a associação entre Role e Users
def test_role_users_association(db_session):
    role = Role(name="Manager", friendly_name="Project Manager")
    db_session.add(role)
    db_session.commit()

    user = Users(email="example@example.com", password='abc123', first_name="John", last_name="Doe", role_id=role.id)
    db_session.add(user)
    db_session.commit()

    # Verifique se o usuário está associado ao papel
    added_user = db_session.query(Users).filter_by(email="example@example.com").first()
    assert added_user.role.name == "Manager"
    
    
# Teste para deletar um Role
def test_delete_role(db_session):
    role = Role(name="Intern", friendly_name="Intern")
    db_session.add(role)
    db_session.commit()

    db_session.delete(role)
    db_session.commit()

    deleted_role = db_session.query(Role).filter_by(name="Intern").first()
    assert deleted_role is None
    
    
# Teste para criar um novo Department
def test_create_department(db_session):
    new_department = Department(name="HR")
    db_session.add(new_department)
    db_session.commit()

    # Verifique se o novo Department foi adicionado ao banco de dados
    added_department = db_session.query(Department).filter_by(name="HR").first()
    assert added_department is not None
    assert added_department.name == "HR"
    
    
# Teste para verificar a associação entre Department e Users
def test_department_users_association(db_session):
    department = Department(name="Finance")
    db_session.add(department)
    db_session.commit()

    user = Users(email="finance@example.com", password='abc123', first_name="Alice", last_name="Bob", department_id=department.id)
    db_session.add(user)
    db_session.commit()

    # Verifique se o usuário está associado ao departamento
    added_user = db_session.query(Users).filter_by(email="finance@example.com").first()
    assert added_user.department.name == "Finance"
    
    # Teste para verificar a associação entre Department e Role
def test_department_role_association(db_session):
    department = Department(name="Engineering")
    db_session.add(department)
    db_session.commit()

    role = Role(name="Engineer", friendly_name="Software Engineer")
    role.departments.append(department)
    db_session.add(role)
    db_session.commit()

    # Verifique se o departamento está associado ao papel
    added_role = db_session.query(Role).filter_by(name="Engineer").first()
    assert department in added_role.departments
    
    # Teste para atualizar um Department
def test_update_department(db_session):
    department = Department(name="Support")
    db_session.add(department)
    db_session.commit()

    updated_department = db_session.query(Department).filter_by(name="Support").first()
    updated_department.name = "Customer Support"
    db_session.commit()

    reloaded_department = db_session.query(Department).filter_by(name="Customer Support").first()
    assert reloaded_department is not None
    assert reloaded_department.name == "Customer Support"
    
    # Teste para deletar um Department
def test_delete_department(db_session):
    department = Department(name="Temporary")
    db_session.add(department)
    db_session.commit()

    db_session.delete(department)
    db_session.commit()

    deleted_department = db_session.query(Department).filter_by(name="Temporary").first()
    assert deleted_department is None
    
# Testes para a classe EmployeeContract
def test_create_employee_contract(db_session):
    user = Users(email="john@example.com", password='abc123', first_name="John", last_name="Doe")
    db_session.add(user)
    db_session.commit()

    new_contract = EmployeeContract(
        active=True,
        user_id=user.id,
        type='Por mês',
        salary=3000.00,
        date_joined=datetime.now()
    )
    db_session.add(new_contract)
    db_session.commit()

    added_contract = db_session.query(EmployeeContract).filter_by(user_id=user.id).first()
    assert added_contract is not None
    assert added_contract.salary == 3000.00
    assert added_contract.active is True
    
def test_employee_contract_relationship(db_session):
    user = Users(email="sarah@example.com", password='abc123', first_name="Sarah", last_name="Connor")
    db_session.add(user)
    db_session.commit()

    contract = EmployeeContract(
        active=True,
        user_id=user.id,
        type='Por mês',
        salary=4500.00,
        date_joined=datetime.now()
    )
    db_session.add(contract)
    db_session.commit()

    added_user = db_session.query(Users).filter_by(email="sarah@example.com").first()
    assert added_user.employee_contracts[0].salary == 4500.00

@pytest.fixture
def user_and_contract(db_session):
    """Cria um usuário e um contrato associado para teste."""
    # Criação do usuário
    user = Users(
        email="sarah@example.com",
        cpf="12345678901",
        first_name="Sarah",
        last_name="Connor",
        birth_date=datetime.now(),
        # Adicione os demais campos necessários conforme o modelo Users
    )
    db_session.add(user)
    db_session.commit()

    # Criação do contrato associado ao usuário
    contract = EmployeeContract(
        user_id=user.id,
        active=True,
        type="Por mês",
        salary=4000.00,
        date_joined=datetime.now(),
        # Adicione os demais campos necessários conforme o modelo EmployeeContract
    )
    db_session.add(contract)
    db_session.commit()

    return user, contract

def test_update_employee_contract(db_session):
    # Criação do usuário e do contrato no mesmo teste
    user = Users(email="sarah@example.com", cpf="12345678901", password='abc123', first_name="Sarah", last_name="Connor", birth_date=datetime.now())
    db_session.add(user)
    db_session.commit()

    contract = EmployeeContract(active=True, user_id=user.id, type='Por mês', salary=3000.00, date_joined=datetime.now())
    db_session.add(contract)
    db_session.commit()

    # Verifica se o contrato existe e atualiza
    contract = db_session.query(EmployeeContract).filter_by(user_id=user.id).first()
    assert contract is not None, "Contrato do usuário não encontrado no banco de dados."

    contract.salary = 5000.00
    db_session.commit()

    # Verifica a atualização
    updated_contract = db_session.query(EmployeeContract).filter_by(user_id=user.id).first()
    assert updated_contract.salary == 5000.00

def test_create_and_retrieve_client(db_session):
    """
    Test the creation and retrieval of a Client instance.
    Ensures that a client can be successfully added to the database and retrieved,
    with all data correctly stored.
    """
    # Creating a new Client instance
    client = Client(
        business_type='Academia',
        cnpj='12345678901234',
        is_instagram_connected_facebook_page=True,
        is_active_impulsionamento_instagram=True,
        legal_name='Academy Fitness Ltda',
        logo_url='http://example.com/logo.png',
        n_contracted_creative_assets=5,
        name='Academy Fitness',
        user_id=None  # Assuming this can be null temporarily
    )
    # Adding the new client to the database session and committing
    db_session.add(client)
    db_session.commit()

    # Retrieving the first Client instance from the database
    retrieved = db_session.query(Client).filter_by(cnpj='12345678901234').first()
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved.name == 'Academy Fitness'
    assert retrieved.business_type == 'Academia'
    assert retrieved.is_active_impulsionamento_instagram is True
def test_create_and_retrieve_user_client(db_session):
    """
    Test the creation and retrieval of a UserClient instance.
    Ensures that a user client can be successfully added to the database and retrieved,
    with all data correctly stored, and linked to a client.
    """
    # Creating a new Client instance
    client = Client(
        business_type='Clínica',
        cnpj='23456789012345',
        is_instagram_connected_facebook_page=False,
        legal_name='Clinic Care Ltda',
        logo_url='http://example.com/clinic_logo.png',
        name='Clinic Care',
        user_id=None  # Assuming this can be null temporarily
    )
    db_session.add(client)
    db_session.commit()

    # Creating a new UserClient instance
    legal_representative = UserClient(
        full_name="Jane Doe",
        position="Legal Representative",
        cpf="12345678901",
        phone="1234567890",
        email="jane.doe@example.com",
        is_legal_representative=True,
        is_financial_representative=False
    )
    financial_representative = UserClient(
        full_name="John Smith",
        position="Financial Representative",
        cpf="10987654321",
        phone="0987654321",
        email="john.smith@example.com",
        is_legal_representative=False,
        is_financial_representative=True
    )
    # Associating the representatives with the client
    client.users.append(legal_representative)
    client.users.append(financial_representative)
    db_session.add(legal_representative)
    db_session.add(financial_representative)
    db_session.commit()

    # Retrieving the first UserClient instance from the database
    retrieved_legal = db_session.query(UserClient).filter_by(cpf='12345678901').first()
    retrieved_financial = db_session.query(UserClient).filter_by(cpf='10987654321').first()
    
    # Asserting that the data retrieved matches the data that was initially created
    assert retrieved_legal.full_name == "Jane Doe"
    assert retrieved_legal.is_legal_representative is True
    assert retrieved_legal.is_financial_representative is False
    assert retrieved_legal.clients[0].name == 'Clinic Care'
    
    assert retrieved_financial.full_name == "John Smith"
    assert retrieved_financial.is_legal_representative is False
    assert retrieved_financial.is_financial_representative is True
    assert retrieved_financial.clients[0].name == 'Clinic Care'

    
    
# def test_delete_employee_contract(db_session):
#     user = db_session.query(Users).filter_by(email="john@example.com").first()
#     contract = db_session.query(EmployeeContract).filter_by(user_id=user.id).first()
#     db_session.delete(contract)
#     db_session.commit()

#     deleted_contract = db_session.query(EmployeeContract).filter_by(user_id=user.id).first()
#     assert deleted_contract is None