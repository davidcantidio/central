from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.database import engine
from models.models import Department, Users, Role
from .crud_logging import get_or_create, logger

def create_user(email, first_name, last_name, password, username, cpf, department_id=None, role_id=None, **other_fields):
    with Session(bind=engine) as session:
        user, created = get_or_create(session, Users, email=email)
        
        if created:
            user.first_name = first_name
            user.last_name = last_name
            user.password = password
            user.username = username
            user.cpf = cpf

            for field, value in other_fields.items():
                setattr(user, field, value)

            if department_id:
                department = session.query(Department).get(department_id)
                if department:
                    user.department = department
                else:
                    logger.error(f"Departamento ID '{department_id}' não encontrado.")
                    session.rollback()
                    return

            if role_id:
                role = session.query(Role).get(role_id)
                if role:
                    user.role = role
                else:
                    logger.error(f"Role ID '{role_id}' não encontrado.")
                    session.rollback()
                    return

            try:
                session.commit()
                logger.info(f"Usuário '{first_name} {last_name}' criado com sucesso.")
            except IntegrityError as ie:
                session.rollback()
                logger.error(f"Erro de integridade ao criar usuário: {ie}")
            except SQLAlchemyError as se:
                session.rollback()
                logger.error(f"Erro do SQLAlchemy ao criar usuário: {se}")
            except Exception as e:
                session.rollback()
                logger.error(f"Erro desconhecido ao criar usuário: {e}")
        else:
            logger.info(f"Usuário com email '{email}' já existe.")

def generate_email(first_name):
    return f"{first_name.lower()}@mandalamarketing.com.br"

def generate_username(first_name):
    return first_name.lower()

def generate_unique_cpf(index):
    return f"{index:011d}"

def insert_users():
    users_data = [
        "Adriele",
        "Thamile",
        "Duda",
        "Thamile",
        "Thamile",
        "Daniel",
        "Adriele",
        "Adriele",
        "Duda",
        "Thamile",
        "Vitória",
        "Duda",
        "Daniel",
        "Adriele",
        "Daniel",
        "Daniel",
        "Adriele",
        "Daniel",
        "Vitória",
        "Thamile"
    ]

    department_id = 6  # ID do departamento 'Social Media'
    role_id = 2  # ID do role 'Social Media'
    cpf_index = 1

    for entry in users_data:
        name = entry.strip()
        first_name = name
        last_name = ''

        email = generate_email(first_name)
        username = generate_username(first_name)
        cpf = generate_unique_cpf(cpf_index)
        cpf_index += 1
        create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password='mandala123',
            username=username,
            cpf=cpf,
            department_id=department_id,
            role_id=role_id,
            birth_date=date(2000, 1, 1)
        )

if __name__ == "__main__":
    insert_users()
