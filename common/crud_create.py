import json
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from common.database import engine
from common.models import Base, Department, Users, Role, Client, Liaison
from .crud_logging import get_or_create, logger

# Certifique-se de que todas as tabelas são criadas
Base.metadata.create_all(bind=engine)

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
                department = session.get(Department, department_id)
                if department:
                    user.department = department
                else:
                    logger.error(f"Departamento ID '{department_id}' não encontrado.")
                    session.rollback()
                    return

            if role_id:
                role = session.get(Role, role_id)
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
    users_data = {
        3: {  # ID do departamento 'Criação'
            5: [  # ID do role 'Copywriter'
                "Paloma / Fabianne / Ana Luísa",
                "Paloma / Fabianne",
                "Cândida / Monique",
                "Crisler / Guilherme",
                "Isabela / Gabriela",
                "Cândida / Monique",
                "Paloma / Fabianne / Ana Luísa",
                "Paloma / Fabianne / Ana Luísa",
                "Crisler / Guilherme",
                "Mariana M. / Maiane",
                "Mariana M. / Maiane",
                "Beatriz / Gabriela",
                "Cândida / Monique",
                "Mariana M. / Maiane",
                "Crisler / Guilherme",
                "Crisler / Guilherme",
                "Crisler / Guilherme",
                "Cândida / Monique",
                "Paloma / Fabianne / Ana Luísa",
                "Impulsionamento Plus",
                "Júlia / Paloma",
                "Mariana M. / Maiane",
                "Crisler / Guilherme",
                "Mariana Caldas",
                "Desconhecido"
            ]
        },
        6: {  # ID do departamento 'Social Media'
            2: [  # ID do role 'Social Media'
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
        }
    }

    cpf_index = 1

    for department_id, roles in users_data.items():
        for role_id, users in roles.items():
            for entry in users:
                names = [name.strip() for name in entry.split('/')]
                for name in names:
                    if name.lower() == 'ana luísa':
                        first_name = 'Ana Luísa'
                        last_name = ''
                    elif name.lower() == 'impulsionamento plus':
                        first_name = 'Impulsionamento'
                        last_name = 'Plus'
                    elif name == 'Mariana Caldas':
                        first_name = 'Mariana'
                        last_name = 'Caldas'
                    else:
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

def create_role(name, friendly_name, department_names):
    with Session(bind=engine) as session:
        role, created = get_or_create(session, Role, name=name, friendly_name=friendly_name)
        
        if created:
            try:
                session.flush()  # Assegura que 'role' tem um 'id' antes de continuar
                for dept_name in department_names:
                    department, _ = get_or_create(session, Department, name=dept_name)
                    if department:
                        role.departments.append(department)

                session.commit()
                logger.info(f"Role '{name}' criado e associado aos departamentos.")
            except IntegrityError as ie:
                session.rollback()
                logger.error(f"Integrity error ao criar role: {ie}")
            except SQLAlchemyError as se:
                session.rollback()
                logger.error(f"SQLAlchemy error: {se}")
            except Exception as e:
                session.rollback()
                logger.error(f"Erro desconhecido ao criar role: {e}")
        else:
            logger.info(f"Role '{name}' já existe.")

def create_department(name):
    with Session(bind=engine) as session:
        department, created = get_or_create(session, Department, name=name)
        
        if created:
            try:
                session.commit()
                logger.info(f"Departamento '{name}' criado com sucesso.")
            except IntegrityError as ie:
                session.rollback()
                logger.error(f"Integrity error ao criar departamento: {ie}")
            except SQLAlchemyError as se:
                session.rollback()
                logger.error(f"SQLAlchemy error: {se}")
            except Exception as e:
                session.rollback()
                logger.error(f"Erro desconhecido ao criar departamento: {e}")
        else:
            logger.info(f"Departamento '{name}' já existe.")

def create_client(data):
    with Session(bind=engine) as session:
        # Criação do cliente
        client, created = get_or_create(session, Client, cnpj=data.get('cnpj'))
        
        if created:
            client.cpf = data.get('cpf')
            client.legal_name = data.get('legal_name')
            client.name = data.get('name')
            client.email = data.get('invoice_recipients_email')
            client.postal_code = data.get('CEP')
            client.business_phone = data.get('business_phone')
            client.phone = data.get('phone')
            client.google_ads_account_id = data.get('google_ads_account_id')
            client.fb_page_id = data.get('fb_page_id')
            client.id_instagram = data.get('id_instagram')
            client.hashtag_padrao = data.get('hashtag_padrao')
            client.id_linkedin = data.get('id_linkedin')
            client. n_monthly_contracted_creative_mandalecas = data.get(' n_monthly_contracted_creative_mandalecas')
            client.n_monthly_contracted_content_production_mandalecas = data.get('n_monthly_contracted_producao_conteudo_mandalecas')
            client.n_monthly_contracted_format_adaptation_mandalecas = data.get('n_monthly_contracted_adaptacao_mandalecas')
            client.n_monthly_contracted_stories_mandalecas = data.get('n_monthly_contracted_stories_mandalecas')
            client.n_monthly_contracted_reels_mandalecas = data.get('n_monthly_contracted_reels_mandalecas')
            client.n_monthly_contracted_stories_repost_mandalecas = data.get('n_monthly_contracted_stories_repost_mandalecas')
            client.n_monthly_contracted_cards_mandalecas = data.get('n_monthly_contracted_cards_mandalecas')
            client.n_monthly_contracted_feed_tiktok_mandalecas = data.get('n_monthly_contracted_feed_tiktok_mandalecas')
            client.n_monthly_contracted_feed_linkedin_mandalecas = data.get('n_monthly_contracted_feed_linkedin_mandalecas')
            client.id_tiktok = data.get('id_tiktok')
            client.normalized_name = data.get('normalized_name')

            # Campos contratuais
            client.n_monthly_contracted_creative_mandalecas = 6
            client.n_monthly_contracted_format_adaptation_mandalecas = 2
            client.n_monthly_contracted_production_content_mandalecas = 5

            # Outros campos adicionais
            client.marketing = data.get('marketing')
            client.verba_mensal_impulsionamento = data.get('verba_mensal_impulsionamento')
            client.copy = data.get('copy')
            client.n_monthly_contracted_stories_mandalecas = data.get('n_posts_contratados_stories_instagram')
            client.n_monthly_contracted_reels_mandalecas= data.get('n_posts_contratados_reels_instagram')
            client.n_monthly_contracted_stories_repost_mandalecas = data.get('n_posts_contratados_feed_linkedin')
            client.n_monthly_contracted_feed_linkedin_mandalecas= data.get('n_posts_contratados_stories_instagram')
            client.n_monthly_contracted_feed_tiktok_mandalecas = data.get('n_posts_contratados_feed_facebook')
            client.n_monthly_contracted_creative_mandalecas = data.get('n_posts_contratados_feed_tiktok')
            client.url_img_logo = data.get('url_img_logo')
            client.ativo = data.get('ativo')
            client.impulsionamento = data.get('Impulsionamento')
            client.trafego_pago = data.get('trafego_pago')
            client.linkedin = data.get('linkedin')
            client.permissoes = data.get('permissoes')
            client.fb_ad_account_id = data.get('fb_ad_account_id')
            client.redes_sociais = data.get('redes_sociais')
            client.n_usuario_instagram = data.get('n_usuario_instagram')

            session.add(client)

        # Verificar e criar representantes legais
        if data.get('legal_representative_full_name'):
            legal_representative = Liaison(
                full_name=data.get('legal_representative_full_name'),
                cpf=data.get('legal_representative_cpf'),
                rg=data.get('legal_representative_rg'),
                street_name=data.get('legal_representative_street_name'),
                number=data.get('legal_representative_number'),
                complement=data.get('legal_representative_complement'),
                neighbourhood=data.get('legal_representative_neighbourhood'),
                city=data.get('legal_representative_city'),
                state=data.get('legal_representative_state'),
                birthday=data.get('legal_representative_birth_date'),
                postal_code=data.get('CEP'),
                phone=data.get('legal_representative_phone'),
                email=data.get('legal_representative_e_mail'),
                position=data.get('legal_representative_position'),
                title='Legal Representative',
                legal_representative=True,
                finances_representative=False
            )
            legal_representative.clients.append(client)
            session.add(legal_representative)

        # Verificar e criar representantes financeiros
        if data.get('finance_representative_full_name'):
            finance_representative = Liaison(
                full_name=data.get('finance_representative_full_name'),
                cpf=data.get('finance_representative_cpf'),
                rg=data.get('finance_representative_rg'),
                street_name=data.get('finance_representative_street_name'),
                number=data.get('finance_representative_number'),
                complement=data.get('finance_representative_complement'),
                neighbourhood=data.get('finance_representative_neighbourhood'),
                city=data.get('finance_representative_city'),
                state=data.get('finance_representative_state'),
                birthday=data.get('finance_representative_birth_date'),
                postal_code=data.get('CEP'),
                phone=data.get('finance_representative_phone'),
                email=data.get('finance_representative_e_mail'),
                position=data.get('finance_representative_position'),
                title='Financial Representative',
                legal_representative=False,
                finances_representative=True
            )
            finance_representative.clients.append(client)
            session.add(finance_representative)
        
        try:
            session.commit()
            logger.info(f"Cliente '{client.name}' criado com sucesso.")
        except IntegrityError as ie:
            session.rollback()
            logger.error(f"Erro de integridade ao criar cliente: {ie}")
        except SQLAlchemyError as se:
            session.rollback()
            logger.error(f"Erro do SQLAlchemy ao criar cliente: {se}")
        except Exception as e:
            session.rollback()
            logger.error(f"Erro desconhecido ao criar cliente: {e}")


def process_data(json_data):
    for client_data in json_data:
        create_client(client_data)

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

if __name__ == "__main__":
    create_department('Marketing')
    create_department('RH')
    create_department('Criação')
    create_department('Produção')
    
    create_role('coordinator', 'Coordenador', ['Marketing', 'RH', 'Tráfego Pago', 'Produção', 'Redes Sociais'])
    create_role('analyst', 'Analista', ['Marketing', 'RH', 'Tráfego Pago', 'Produção', 'Redes Sociais'])
    create_role('assistant', 'Assistente', ['Marketing', 'RH', 'Tráfego Pago', 'Produção', 'Redes Sociais'])
    create_role('art_director', 'Dir. de Arte', ['Criação'])
    create_role('copywritter', 'Copywritter', ['Criação'])
    insert_users()
    
    # Carregar dados de clientes a partir do arquivo JSON
    json_filepath = '/home/debrito/Documentos/central/common/clientes.json'
    json_data = load_json(json_filepath)
    process_data(json_data)
