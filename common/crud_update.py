#Crud
from sqlalchemy.orm import declarative_base, Session
from datetime import date
from sqlalchemy import select
from models.database import engine 
from sqlalchemy.orm import Session, joinedload
from models.models import Role, Department, role_department_association, Users
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

# Configuração básica do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_user(id,
                addr_cep = None,
                addr_complement = None,
                addr_neighbourhood = None,
                addr_number = None,
                addr_street = None,
                alternative_phone = None,
                birth_date = None,
                cpf = None,
                created_at = None,
                updated_at = None,
                department_id = None,
                email = None,
                first_name = None,
                password = None,
                instagram = None,
                last_name = None,
                linkedin = None,
                n_jobs_contrato = None,
                price_per_job = None,
                profile_pic_url = None,
                role_id = None,
                username = None,
                whatsapp = None):
    with Session(bind=engine) as session:
        sql_query = select(Users).filter_by(id=id)
        users = session.execute(sql_query).fetchall()
        for user in users:

            if addr_complement:
                user[0].addr_complement = addr_complement

            if addr_neighbourhood:
                user[0].addr_neighbourhood = addr_neighbourhood

            if addr_number:
                user[0].addr_number = addr_number

            if addr_street:
                user[0].addr_street = addr_street

            if alternative_phone:
                user[0].alternative_phone = alternative_phone

            if birth_date:
                user[0].birth_date = birth_date

            if cpf:
                user[0].cpf = cpf

            if created_at:
                user[0].created_at = created_at

            if updated_at:
                user[0].updated_at = updated_at

            if department_id:
                user[0].department_id = department_id

            if email:
                user[0].email = email

            if first_name:
                user[0].first_name = first_name

            if password:
                user[0].password = password

            if id:
                user[0].id = id

            if instagram:
                user[0].instagram = instagram

            if last_name:
                user[0].last_name = last_name

            if linkedin:
                user[0].linkedin = linkedin

            if n_jobs_contrato:
                user[0].n_jobs_contrato = n_jobs_contrato

            if price_per_job:
                user[0].price_per_job = price_per_job

            if profile_pic_url:
                user[0].profile_pic_url = profile_pic_url

            if username:
                user[0].username = username

            if whatsapp:
                user[0].whatsapp = whatsapp

            if addr_cep:
                user[0].nome= addr_cep
        session.commit()
            
if __name__ == '__main__':
    update_user(id=1, addr_cep='59000123')
