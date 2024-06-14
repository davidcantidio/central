from .database import Base, init_db
from sqlalchemy import create_engine, DateTime, Column, DECIMAL, Integer, String, Boolean, ForeignKey, Enum, TIMESTAMP, Numeric, CheckConstraint, JSON, Date, DECIMAL, Text, Float
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Index, event
from enum import Enum
from sqlalchemy.types import Enum as SQLAlchemyEnum


# Tabela associativa para a relação many-to-many entre Role e Department
role_department_association = Table(
    'role_department', Base.metadata,
    Column('department_id', Integer, ForeignKey('departments.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Tabela associativa para a relação muitos-para-muitos entre Client e Liaison
client_liaison_association = Table(
    'client_liaison_association', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id')),
    Column('liaison_id', Integer, ForeignKey('liaisons.id'))
)

# Tabela associativa para a relação muitos-para-muitos entre Client e Users para account_executives
client_account_executives_association = Table(
    'client_account_executives', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# Tabela associativa para a relação muitos-para-muitos entre Client e Users para social_media
client_social_media_association = Table(
    'client_social_media', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# Tabela associativa para a relação muitos-para-muitos entre Client e Users para copywriter
client_copywriter_association = Table(
    'client_copywriter', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# Tabela associativa para a relação muitos-para-muitos entre Client e Service
client_services_association = Table('client_services', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True)
)


class MetaAdsCTA(Base):
    __tablename__ = 'meta_ads_ctas'
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    name = Column(String, nullable=False, unique=True)
    friendly_name = Column(String, nullable=False)
class Role(Base):
    """
    Representa uma ou função dentro de um departamento, por exemplo: analista, gerente ou assistente.


    Relacionamentos:
        departments (relationship): Uma lista de departamentos associados a este papel. 
                                    Representa uma relação many-to-many entre `Role` e `Department`.
        users (relationship): Uma lista de usuários associados a este papel. 
    """
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    friendly_name = Column(String, nullable=False)
    # Relacionamento many-to-many com Department
    departments = relationship(
        "Department",
        secondary=role_department_association,
        back_populates="roles"
    )
    employees = relationship("Users", back_populates="role")
    role_scopes = relationship("RoleDepartmentScope", back_populates="role")

    def __repr__(self):
            return f"Role(id={self.id}, name='{self.name}', employees_count={len(self.employees)})"

class RoleDepartmentScope(Base):
    """
    Represents the specific scope of activities (activity_scopes) associated with a Role within a particular Department.

    This association class enables a many-to-many relationship between Roles and Departments, with additional data on activity scopes.
    """
    __tablename__ = 'role_department_scopes'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)  # Links to the Role entity
    department_id = Column(Integer, ForeignKey('departments.id'), primary_key=True)  # Links to the Department entity
    activity_scopes = Column(JSON)  # Stores the specific activities allowed for this role in the department

    # Establish relationships
    role = relationship("Role", back_populates="role_scopes")  # Back-populates to Role entity
    department = relationship("Department", back_populates="department_scopes")  # Back-populates to Department entity

    def __repr__(self):
        return f"<RoleDepartmentScope(role_id={self.role_id}, department_id={self.department_id}, activity_scopes={self.activity_scopes})>"

class Department(Base):
    """
    Represents a department within an organization.
    """
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)  # Unique identifier for the department
    created_at = Column(TIMESTAMP, default=datetime.now)  # Creation date and time of the department
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)  # Date and time of the last update
    name = Column(String(255), unique=True, nullable=False)  # Name of the department, unique and mandatory

    # Relationships:
    employees = relationship("Users", back_populates="department", foreign_keys="[Users.department_id]")
    roles = relationship("Role", secondary=role_department_association, back_populates="departments")  # Roles associated with the department
    department_scopes = relationship("RoleDepartmentScope", back_populates="department")
 
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"

class EmployeeContract(Base):
    __tablename__ = 'employee_contract'

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('users.id'))
    type = Column(SQLAlchemyEnum('Por job', 'Por mês', 'Por jornada', name='contract_types'), nullable=False)  # Type of the contract
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    active = Column(Boolean, default=True)

    # Relationship back to the User
    employee = relationship("Users", back_populates="employee_contracts")

    def __repr__(self):
        return f"<EmployeeContract(id={self.id}, type='{self.type}', active={self.active}, employee_id={self.employee_id})>"


    def __repr__(self):
        return f"<EmployeeContract(id={self.id}, type='{self.type}', active={self.active}, user_id={self.user_id})>"
class Users(Base):
    __tablename__ = 'users'

    # Personal information
    addr_cep = Column(String(10))  # Postal code of the user's address
    addr_complement = Column(String(255))  # Additional address information
    addr_neighbourhood = Column(String(255))  # Neighbourhood of the user's address
    addr_number = Column(String(10))  # House number of the user's address
    addr_street = Column(String(255))  # Street name of the user's address
    alternative_phone = Column(String(20))  # An alternative phone number for the user
    birth_date = Column(Date) 
    aliases = Column(JSON)
    cpf = Column(String(11), unique=True)  # User's CPF number (specific to Brazilian users)
    created_at = Column(TIMESTAMP, default=datetime.now)  # Timestamp when the user was created
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)  # Timestamp when the user was updated
    
    department_id = Column(Integer, ForeignKey('departments.id'))  # Department ID the user belongs to
    email = Column(String(255), unique=True, nullable=False)  # User's email address
    first_name = Column(String(40), nullable=False)  # First name of the user
    password = Column(String(40), nullable=False)
    id = Column(Integer, primary_key=True)  # Unique identifier for the user
    instagram = Column(String(255))  # User's Instagram username
    last_name = Column(String(40), nullable=False)  # Last name of the user
    linkedin = Column(String(255))  # User's LinkedIn profile link
    n_jobs_contrato = Column(Integer, CheckConstraint('n_jobs_contrato >= 0'))  # Number of jobs under the user's contract
    price_per_job = Column(Numeric(10, 2))  # Price per job for the user
    profile_pic_url = Column(String(255))  # URL to the user's profile picture
    role_id = Column(Integer, ForeignKey('roles.id'))  # Role ID associated with the user
    username = Column(String(255), unique=True)  # User's chosen username
    whatsapp = Column(String(255))  # User's WhatsApp number

    # Relationships
    department = relationship("Department", back_populates="employees")
    employee_contracts = relationship("EmployeeContract", back_populates="employee", cascade="all, delete, delete-orphan")  # Relacionamento um-para-muitos
    role = relationship("Role", back_populates="employees")
    reports = relationship("Report", back_populates="author")
    briefing_redes_sociais = relationship("BriefingRedesSociais", back_populates="author", foreign_keys="[BriefingRedesSociais.author_id]")
    products = relationship("Product", back_populates="author")
    briefings_trafego_pago = relationship("BriefingTrafegoPago", foreign_keys="[BriefingTrafegoPago.author_id]")
    briefing_redes_sociais_updates = relationship("BriefingRedesSociais", back_populates="updater", foreign_keys="[BriefingRedesSociais.last_updated_by]")
    updated_briefings_trafego_pago = relationship("BriefingTrafegoPago", back_populates="updater", foreign_keys="[BriefingTrafegoPago.last_updated_by]")
    created_plans_trafego_pago = relationship("PlanTrafegoPago", back_populates="author")
    user_in_charge_jobs = relationship("DeliveryControlCreative", foreign_keys='DeliveryControlCreative.user_in_charge_id', back_populates="user_in_charge")
    requested_jobs = relationship("DeliveryControlCreative", foreign_keys='DeliveryControlCreative.requested_by_id', back_populates="requested_by")
    user_in_charge_redes_sociais = relationship("DeliveryControlRedesSociais", foreign_keys='DeliveryControlRedesSociais.user_in_charge_id', back_populates="user_in_charge")
    requested_redes_sociais = relationship("DeliveryControlRedesSociais", foreign_keys='DeliveryControlRedesSociais.requested_by_id', back_populates="requested_by")



    def __repr__(self):
        return f"<Users(id={self.id}, name='{self.first_name} {self.last_name}')>"
class Liaison(Base):
    __tablename__ = 'liaisons'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    cpf = Column(String(11), unique=True)
    rg = Column(String(20))
    street_name = Column(String(255))
    number = Column(String(10))
    complement = Column(String(255))
    neighbourhood = Column(String(255))
    city = Column(String(255))
    state = Column(String(2))
    birthday = Column(Date)
    postal_code = Column(String(10))
    phone = Column(String(20))
    email = Column(String(255))
    position = Column(String(255))  # legal_representative_position
    title = Column(SQLAlchemyEnum('Legal Representative', 'Financial Representative', 'Other', name='liaison_titles', nullable=False))  # Type of the contract
    legal_representative = Column(Boolean)
    finances_representative = Column(Boolean)
    
    # Estabelecer relacionamento com Client
    clients = relationship("Client", secondary=client_liaison_association, back_populates="liaisons")

class Client(Base):
    __tablename__ = 'clients'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    business_type = Column(SQLAlchemyEnum('Imob', 'Academia', 'Clínica', 'Político'), index=True)
    cnpj = Column(String(18), unique=True)
    cpf = Column(String(11), unique=True)
    aliases = Column(JSON)
    is_instagram_connected_facebook_page = Column(Boolean, default=False)
    is_active_impulsionamento_instagram = Column(Boolean, default=False)
    is_active_impulsionamento_linkedin = Column(Boolean, default=False)
    is_active_impulsionamento_tiktok = Column(Boolean, default=False)
    is_active_instagram = Column(Boolean, default=False)
    is_active_linkedin = Column(Boolean, default=False)
    is_active_tiktok = Column(Boolean, default=False)
    is_active_google_ads = Column(Boolean, default=False)
    invoice_recipients_emails = Column(JSON)
    foundation_date = Column(Date)
    due_charge_date = Column(Date)
    legal_name = Column(Text)
    logo_url = Column(String(255))
    n_monthly_contracted_creative_mandalecas = Column(Float, default=0)
    n_monthly_contracted_format_adaptation_mandalecas = Column(Float, default=0)
    n_monthly_contracted_content_production_mandalecas = Column(Float, default=0)
    n_monthly_contracted_stories_mandalecas = Column(Float, default=0)
    n_monthly_contracted_feed_linkedin_mandalecas = Column(Float, default=0)
    n_monthly_contracted_feed_tiktok_mandalecas = Column(Float, default=0)
    n_monthly_contracted_stories_repost_mandalecas = Column(Float, default=0)
    n_monthly_contracted_reels_mandalecas = Column(Float, default=0)
    n_monthly_contracted_cards_mandalecas = Column(Float, default=0)
    accumulated_creative_mandalecas = Column(Float, default=0)
    accumulated_format_adaptation_mandalecas = Column(Float, default=0)
    accumulated_content_mandalecas = Column(Float, default=0)
    accomulated_feed_linkedin_mandalecas = Column(Float, default=0)
    accumulated_feed_tiktok_mandalecas = Column(Float, default=0)
    accumulated_stories_mandalecas = Column(Float, default=0)
    accumulated_stories_repost_mandalecas = Column(Float, default=0)
    accumulated_reels_mandalecas = Column(Float, default=0)
    accumulated_cards_mandalecas = Column(Float, default=0)
    name = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    date_start_communication_plan = Column(Date)
    date_end_communication_plan = Column(Date)
    date_presentation_communication_plan = Column(Date)
    postal_code = Column(String(10))  # CEP
    business_phone = Column(String(20))
    phone = Column(String(20))
    email = Column(String(255))
    date_start_contract = Column(Date)
    date_end_contract = Column(Date)
    initial_goal = Column(Text)
    final_goal = Column(Text)
    website = Column(String(255))
    business_area = Column(String(255))
    brand_suggestions = Column(Text)
    monthly_investment = Column(Float)
    facebook_page_id = Column(String(255))
    google_ads_account_id = Column(String(255))
    instagram_profile_id = Column(String(255))
    linkedin_profile_id = Column(String(255))
    tiktok_profile_id = Column(String(255))
    hashtags = Column(JSON)  # Hashtags (JSON field)
    address = Column(String(255))  # Endereço
    address_number = Column(String(10))  # Número do endereço
    address_complement = Column(String(255))  # Complemento do endereço
    address_neighbourhood = Column(String(255))  # Bairro
    city = Column(String(255))  # Cidade
    state = Column(String(2))  # Estado

    # Relacionamentos com outras tabelas
    facebook_pages = relationship("FacebookPage", back_populates="client")
    google_ads_insights = relationship("GoogleAdsInsights", back_populates="client")
    google_ads_profiles = relationship("GoogleAdsProfile", back_populates="client")
    instagram_profile = relationship("InstagramProfile", back_populates="client")
    linkedin_insights = relationship("LinkedinInsights", back_populates="client", primaryjoin="Client.id == LinkedinInsights.client_id")
    linkedin_profiles = relationship("LinkedinProfile", back_populates="client")
    meta_ads_accounts = relationship("MetaAdsAccount", back_populates="client")
    meta_ads_assets = relationship("MetaAdsAssets", back_populates="client")
    meta_ads_insights = relationship("MetaAdsInsights", back_populates="client")
    operand_projects = relationship("OperandProject", back_populates="client")
    services = relationship("Service", secondary=client_services_association, back_populates="clients")
    service_items = relationship("ServiceItem", back_populates="client")
    tiktok_profile = relationship("TikTokProfile", back_populates="client")
    tiktok_insights = relationship("TikTokInsights", back_populates="client")
    reports = relationship("Report", back_populates="client")
    briefing_redes_sociais = relationship("BriefingRedesSociais", back_populates="client")
    products = relationship("Product", back_populates="client")
    briefing_trafego_pago = relationship("BriefingTrafegoPago", back_populates="client")
    plans_trafego_pago = relationship("PlanTrafegoPago", back_populates="client")
    strategic_actions = relationship("StrategicActionsTrafegoPago", back_populates="client")
    profit_analysis = relationship('ProductProfitAnalysis', back_populates='client')
    liaisons = relationship("Liaison", secondary=client_liaison_association, back_populates="clients")
    delivery_control_creatives = relationship("DeliveryControlCreative", back_populates="client")
    delivery_control_redes_sociais = relationship("DeliveryControlRedesSociais", back_populates="client")

    account_executives = relationship("Users", secondary=client_account_executives_association)
    social_media = relationship("Users", secondary=client_social_media_association)
    copywriter = relationship("Users", secondary=client_copywriter_association)

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', business_type='{self.business_type}')>"


# Classe GoogleAdsInsights (mova todas as classes dependentes para baixo da definição das classes de relacionamento)
class GoogleAdsInsights(Base):
    __tablename__ = 'google_ads_insights'
    id = Column(Integer, primary_key=True)
    google_ads_profile_id = Column(String(60), ForeignKey('google_ads_profiles.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))  # Adiciona uma chave estrangeira apontando para clients.id
    insights_data = Column(JSON)
    updated_at = Column(TIMESTAMP, default=datetime.now)

    # Relacionamentos
    profile = relationship("GoogleAdsProfile", back_populates="insights")
    client = relationship("Client", back_populates="google_ads_insights")  # Este é o relacionamento de volta para o Cliente

    def __repr__(self):
        return f"<GoogleAdsInsights(id={self.id})>"

class OperandProject(Base):
    """
    Represents a project managed within the Operand system.
    Each project is associated with a specific client.
    """
    __tablename__ = 'operand_projects'
    
    id = Column(Integer, primary_key=True)  # Unique identifier for the Operand project
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # Links to the client associated with this project
    id_project_operand = Column(String(255), nullable=False, unique=True)  # Operand's unique project ID
    url_project_operand = Column(String(255), nullable=False, unique=True)  # URL to access the project in Operand platform
    name = Column(String(255), nullable=False)  # Name of the Operand project

    # Relationship linking back to the associated client
    client = relationship("Client", back_populates="operand_projects", foreign_keys=[client_id])

    def __repr__(self):
        return f"<OperandProject(id={self.id}, name='{self.name}', client_id={self.client_id})>"

class ServiceItem(Base):
    """
    Represents an item or product offered as part of a Service by Mandala. This could range from specific deliverables in marketing consultancy to distinct content pieces in content production services.
    """
    __tablename__ = 'service_items'
    
    id = Column(Integer, primary_key=True)  # Unique identifier for the service item
    name = Column(String, nullable=False)  # Name of the service item, must be non-null
    price_tokens = Column(Float, CheckConstraint('price_tokens >= 0'), nullable=False)  # Price in tokens, must be non-negative
    price_reals = Column(Float, CheckConstraint('price_reals >= 0'), nullable=False)  # Price in reals, must be non-negative
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)  # Links to the associated Service
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # Links to the Client interested in or purchasing the item

    # Relationships:
    service = relationship("Service", back_populates="service_items")  # The Service this item is part of
    client = relationship("Client", back_populates="service_items")  # The Client who owns or is interested in this item

    def __repr__(self):
        return f"<ServiceItem(id={self.id}, name='{self.name}', price_tokens={self.price_tokens}, price_reals={self.price_reals})>"

class Service(Base):
    """
    Represents a service offered by Mandala, such as Marketing Consultancy, Social Media, Paid Traffic, Creation, and Content Production.
    Each service can be associated with multiple clients and can include various service items.
    """
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)  # Unique identifier for the service
    name = Column(String(90), unique=True, nullable=False)  # Name of the service, must be unique and non-null
    description = Column(Text, nullable=False)  # Detailed description of the service
    icon_html_code = Column(String(255))  # HTML code for the service's icon, optional

    # Relationships:
    clients = relationship("Client", secondary=client_services_association, back_populates="services")  # Many-to-many relation with Client
    service_items = relationship("ServiceItem", back_populates="service")  # One-to-many relation with ServiceItem

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}')>"

class InstagramInsights(Base):
    __tablename__ = 'instagram_insights'

    id = Column(Integer, primary_key=True)  # Unique identifier for the insight record
    instagram_profile_id = Column(String(60), ForeignKey('instagram_profiles.id'), nullable=False)  # Links to associated Instagram profile
    insights_data = Column(JSON)  # Stores the detailed insights data in JSON format
    insight_type = Column(SQLAlchemyEnum('BusiestHours', 'Demographic', 'Media', 'User'), nullable=False)  # Type of insight
    start_date = Column(Date, nullable=False)  # The start date for the collected insights
    end_date = Column(Date, nullable=False)  # The end date for the collected insights
    updated_at = Column(TIMESTAMP, default=datetime.now)  # Timestamp of the last update to the insights

    # Relationship back to the InstagramProfile class
    instagram_profile = relationship("InstagramProfile", back_populates="insights")

class InstagramProfile(Base):
    """
    Represents an Instagram profile associated with a client in the system.
    Stores basic profile information, including official hashtags for branding purposes.
    """
    __tablename__ = 'instagram_profiles'
    id = Column(String(60), primary_key=True)  # Unique Instagram profile ID
    user_name = Column(String(40), nullable=False)  # Instagram username, must be unique
    official_hashtags = Column(JSON)  # Official hashtags associated with the profile, stored as JSON list if multiple
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True, nullable=False)  # Corrected from 'client' to 'client_id'

    updated_at = Column(TIMESTAMP, default=datetime.now)  # Last updated timestamp

    # Relationship back to the Client class
    insights = relationship("InstagramInsights", back_populates="instagram_profile")
    client = relationship("Client", back_populates="instagram_profile")  # Added this line

    
    def __repr__(self):
        return f"<InstagramProfile(id='{self.id}', user_name='{self.user_name}')>"
    
class LinkedinProfile(Base):
    __tablename__ = 'linkedin_profiles'
    id = Column(String(60), primary_key=True)
    user_name = Column(String(40))
    profile_url = Column(String(255))
    official_hashtags = Column(String)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True, nullable=False)

    updated_at = Column(TIMESTAMP, default=datetime.now)
    client = relationship("Client", back_populates="linkedin_profiles")
    insights = relationship("LinkedinInsights", back_populates="linkedin_profile")  # Relacionamento genérico com todas as classes de insights

class GoogleAdsProfile(Base):
    __tablename__ = 'google_ads_profiles'
    id = Column(String(60), primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    
    # Relacionamento - um GoogleAdsProfile tem vários GoogleAdsInsights
    insights = relationship("GoogleAdsInsights", back_populates="profile")
    client = relationship("Client", back_populates="google_ads_profiles")
                            
class LinkedinInsights(Base):
    __tablename__ = 'linkedin_insights'
    id = Column(Integer, primary_key=True)
    linkedin_profile_id = Column(String(60), ForeignKey('linkedin_profiles.id'))
    insights_data = Column(JSON)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    client_id = Column(Integer, ForeignKey('clients.id'))

    # A ligação com LinkedinProfile
    linkedin_profile = relationship("LinkedinProfile", back_populates="insights")
    client = relationship("Client", back_populates="linkedin_insights")

    def __repr__(self):
        # Assumindo que você tenha uma maneira de acessar 'user_name' através de 'linkedin_profile'
        return f"<LinkedinInsights(id={self.id}, profile='{self.linkedin_profile.user_name}')>"
        return f"<LinkedinInsights(id={self.id}, profile='{self.linkedin_profile.user_name}')>"

class TikTokProfile(Base):
    """
    Represents a TikTok profile associated with a client in the system.
    Stores basic profile information including the unique identifier and profile-related data.
    """
    __tablename__ = 'tiktok_profiles'
    id = Column(String(60), primary_key=True)  # Unique TikTok profile ID
    username = Column(String(40), nullable=False)  # TikTok username, must be unique
    biography = Column(Text)  # Biography text from TikTok profile
    followers_count = Column(Integer)  # Number of followers
    following_count = Column(Integer)  # Number of accounts the user is following
    likes_count = Column(Integer)  # Number of likes received across all videos
    video_count = Column(Integer)  # Number of videos posted
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True)

    updated_at = Column(TIMESTAMP, default=datetime.now)  # Last updated timestamp

    # Relationship back to the Client class
    client = relationship("Client", back_populates="tiktok_profile")
    tiktok_insights = relationship("TikTokInsights", back_populates="tiktok_profile")


    def __repr__(self):
        return f"<TikTokProfile(id='{self.id}', username='{self.username}')>"

class TikTokInsights(Base):
    """
    Represents TikTok insights data associated with a TikTok profile.
    This class can be extended by more specific types of TikTok insights.
    """
    __tablename__ = 'tiktok_insights'
    id = Column(Integer, primary_key=True)  # Unique identifier for the insight record
    tiktok_profile_id = Column(String(60), ForeignKey('tiktok_profiles.id'), nullable=False)  # Links to associated TikTok profile
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # New line: Links back to the associated client
    insights_data = Column(JSON)  # Stores the detailed insights data in JSON format
    start_date = Column(Date, nullable=False)  # The start date for the collected insights
    end_date = Column(Date, nullable=False)  # The end date for the collected insights
    updated_at = Column(TIMESTAMP, default=datetime.now)  # Timestamp of the last update to the insights

    # Relationship back to the TikTokProfile class
    tiktok_profile = relationship("TikTokProfile", back_populates="tiktok_insights")
    # New line: Relationship back to the Client class
    client = relationship("Client", back_populates="tiktok_insights")
    tiktok_profile = relationship("TikTokProfile", back_populates="tiktok_insights")


    def __repr__(self):
        return f"<TikTokInsights(id={self.id}, start_date='{self.start_date}', end_date='{self.end_date}')>"

class MetaAdsAssets(Base):
    """
    Represents the Meta (Facebook) advertising assets associated with a client in the system.
    This includes information like business manager ID, pixel ID, and conversion API token.
    """
    __tablename__ = 'meta_ads_assets'
    id = Column(Integer, primary_key=True)
    id_business_manager = Column(Integer, unique=True)
    pixel_id = Column(String(255), unique=True)
    offline_conversions_id = Column(String(255), unique=True)
    conversion_api_token = Column(String(255))
    
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # Links to the associated client

    # Relationships to other Meta ad assets
    client = relationship("Client", back_populates="meta_ads_assets")
    facebook_pages = relationship("FacebookPage", back_populates="meta_ads_asset")
    meta_ads_accounts = relationship("MetaAdsAccount", back_populates="meta_ads_asset")
    product_catalogs = relationship("MetaAdsProductCatalog", back_populates="meta_ads_asset")

    def __repr__(self):
        return f"<MetaAdsAssets(id_business_manager={self.id_business_manager}, pixel_id='{self.pixel_id}')>"

class FacebookPage(Base):
    """
    Represents a Facebook page associated with a client and its corresponding Meta Ads assets.
    This includes the page ID and links to its Meta Ads assets and the associated client.
    """
    __tablename__ = 'facebook_pages'
    id = Column(String(255), primary_key=True)  # Unique Facebook page ID
    meta_ads_asset_id = Column(Integer, ForeignKey('meta_ads_assets.id'), nullable=False)  # Link to associated Meta Ads assets
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # Link to the associated client

    # Relationships
    meta_ads_asset = relationship("MetaAdsAssets", back_populates="facebook_pages")  # Meta Ads assets associated with this Facebook page
    client = relationship("Client", back_populates="facebook_pages")  # The client associated with this Facebook page

    def __repr__(self):
        return f"<FacebookPage(id='{self.id}', client_id={self.client_id})>"

class MetaAdsAccount(Base):
    """
    Represents a Meta (Facebook) Ads account associated with a client, including account ID, linked Meta Ads assets, and insights.
    This class links the account to its Meta Ads assets and the associated client, and it holds the related Meta Ads insights.
    """
    __tablename__ = 'meta_ads_accounts'
    id = Column(String(255), primary_key=True)  # Unique Meta Ads account ID
    meta_ads_asset_id = Column(Integer, ForeignKey('meta_ads_assets.id'), nullable=False)  # Link to the associated Meta Ads assets
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # Link to the associated client

    # Relationships
    meta_ads_asset = relationship("MetaAdsAssets", back_populates="meta_ads_accounts")  # Meta Ads assets associated with this account
    client = relationship("Client", back_populates="meta_ads_accounts")  # The client associated with this Meta Ads account
    meta_ads_insights = relationship("MetaAdsInsights", back_populates="meta_ads_account")  # Insights related to this Meta Ads account

    def __repr__(self):
        return f"<MetaAdsAccount(id='{self.id}', client_id={self.client_id})>"

class MetaAdsProductCatalog(Base):
    """
    Represents a product catalog in Meta Ads, associated with a specific Meta Ads asset.
    Each catalog contains multiple products and is linked to an advertising asset.
    """
    __tablename__ = 'meta_ads_product_catalogs'

    # Unique identifier for the catalog, expected to be a string.
    id = Column(String(255), primary_key=True)

    # JSON structure containing the details of the products. Validate format if necessary.
    catalog = Column(JSON)

    # Links this catalog to a specific Meta Ads asset.
    meta_ads_asset_id = Column(Integer, ForeignKey('meta_ads_assets.id'), nullable=False)

    # Establishes a relationship with the MetaAdsAssets class to access the parent Meta Ads asset.
    meta_ads_asset = relationship("MetaAdsAssets", back_populates="product_catalogs")

    def __repr__(self):

        return f"<MetaAdsProductCatalog(id='{self.id}', meta_ads_asset_id={self.meta_ads_asset_id})>"

class MetaAdsInsights(Base):
    """
    Represents insights data for Meta Ads accounts associated with specific Meta Ads accounts and clients.
    It stores analytical data and performance metrics of advertising campaigns.
    """
    __tablename__ = 'meta_ads_insights'

    id = Column(Integer, primary_key=True)  # Unique identifier for the insights record.
    insights_data = Column(JSON)  # JSON object containing insights and performance metrics.
    updated_at = Column(TIMESTAMP, default=datetime.now, nullable=False)  # Timestamp of the last update to the insights.
    meta_ads_account_id = Column(String(255), ForeignKey('meta_ads_accounts.id'), nullable=False)  # FK to a specific Meta Ads account.
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)  # FK connecting the insights data to a specific client.

    # Relationships
    meta_ads_account = relationship("MetaAdsAccount", back_populates="meta_ads_insights")  # Relationship to MetaAdsAccount.
    client = relationship("Client", back_populates="meta_ads_insights")  # Relationship to Client.

    def __repr__(self):
        return f"<MetaAdsInsights(id={self.id}, meta_ads_account_id='{self.meta_ads_account_id}', client_id={self.client_id})>"
    
class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    date_start = Column(Date)
    date_end = Column(Date)
    title = Column(SQLAlchemyEnum('Assessoria de Marketing', 'Redes Sociais', 'Tráfego Pago', 'Criação', name='report_titles'))
    analysis = Column(Text)
    details = Column(JSON)  # Detalhes específicos do relatório, como número de seguidores, posts, etc.
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    # Relationships
    client = relationship("Client", back_populates="reports")  # The client associated with this report.
    author = relationship("Users", back_populates="reports")  # The author of the report.


    def __repr__(self):
        return f"Relatório: {self.client}, {self.title} - {self.start_date} a {self.end_date}"


class BriefingRedesSociais(Base):
    """
    Represents a social media briefing document within the organization.
    """

    __tablename__ = 'briefings_redes_sociais'
    
    id = Column(Integer, primary_key=True)  # Unique identifier for the briefing.
    client_id = Column(Integer, ForeignKey('clients.id'))  # ID of the associated client.
    author_id = Column(Integer, ForeignKey('users.id'))  # ID of the author of the briefing.
    last_updated_by = Column(Integer, ForeignKey('users.id'))  # ID of the last user to update the briefing.
    target_audience_social_media = Column(Text)  # Description of the target audience for social media.
    main_social_media_objective = Column(Text)  # Main objective of the social media strategy.
    main_content_type_social_media = Column(Text)  # Types of content to focus on in social media.
    how_followers_should_view_company = Column(Text)  # Desired company image on social media.
    brand_personality = Column(Text)  # Brand personality traits to emphasize.
    language_tone = Column(SQLAlchemyEnum('Formal', 'Técnica', 'Informal', 'Descolada', 'Gíria/Regionalismo', 'Pessoal', 'Impessoal', name='language_tones'))  # Preferred language tone.
    social_media_references = Column(Text)  # Examples and references for social media content.
    suggested_research_sources = Column(Text)  # Sources for content and strategy research.
    instagram_login = Column(Text)  # Instagram login details (handle securely).
    instagram_password = Column(Text)  # Instagram password (handle securely).
    free_space = Column(Text)  # Space for additional notes.
    created_at = Column(TIMESTAMP, default=datetime.now)  # Creation timestamp.
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)  # Last updated timestamp.
    is_ready = Column(Boolean)

    # Relationships
    client = relationship("Client", back_populates="briefing_redes_sociais")  # The client associated with this briefing.
    author = relationship("Users", back_populates="briefing_redes_sociais", foreign_keys=[author_id])  # The author of the briefing.
    updater = relationship("Users", back_populates="briefing_redes_sociais_updates", foreign_keys=[last_updated_by])

    def __repr__(self):
        return f"<BriefingRedesSociais(id={self.id}, client_id={self.client_id}, main_objective='{self.main_social_media_objective}')>"

class planoRedesSociais(Base):
    __tablename__ = 'planos_redes_sociais'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    last_updated_by = Column(Integer, ForeignKey('users.id'))
    descritpion = Column(Text)
    publication_date = Column(Date)
    date_start = Column(Date)
    date_finish = Column(Date) 
    date_sent = Column(Date)
    briefing_id = Column(Integer, ForeignKey('briefings_redes_sociais.id'))

class Product(Base):
    """
    Represents a general product within an application, serving as a base class for various product types.
    Utilizes SQLAlchemy's inheritance feature to create product subtypes while sharing common attributes.

    Inheritance:
    Uses SQLAlchemy's 'single table inheritance' feature, storing all subclasses in the same database table.
    The 'type' column differentiates between product types, simplifying the database schema and query logic.
    """
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)  # Unique identifier for each product.
    type = Column(SQLAlchemyEnum('Imob', 'Infoproduto', 'Academia', 'Clínica', 'Varejo', 'E-commerce', name='product_types'))  # Product category.
    product_name = Column(String(255))  # Name of the product.
    description = Column(Text)  # Detailed description of the product.
    target_audience = Column(Text)  # Primary target audience for the product.
    differentials = Column(JSON)  # Distinctive features or advantages of the product.
    objections = Column(JSON)  # Common objections or questions about the product.
    price = Column(DECIMAL(10, 2))  # Price of the product.
    is_membership = Column(Boolean)  # Subscription-based or one-time purchase.
    avg_ticket = Column(DECIMAL(10, 2))  # Expected average revenue per sale or customer.
    avg_insume_cost_per_product = Column(DECIMAL(10, 2))  # Cost to produce or acquire one unit of the product.
    credit_card_fees = Column(DECIMAL(10, 2))  # Fees per sale for credit card payments.
    fulfilment_cost_per_unit = Column(DECIMAL(10, 2))  # Cost for packing and shipping the product.
    total_cost_of_product = Column(DECIMAL(10, 2))  # Total production or acquisition cost.
    percentage_cost = Column(DECIMAL(10, 2))  # Cost of the product as a percentage of the sale price.
    landing_page = Column(String(255))  # URL of the product's landing page.
    inventory_count = Column(Integer)  # Current number of units in stock.
    supplier_id = Column(Integer)  # Foreign key linking to the product's supplier.
    warranty_period = Column(String(255))  # Length of the product warranty.
    return_policy_url = Column(String(255))  # URL to the product's return policy.
    manufacturing_date = Column(Date)  # Date the product was manufactured.
    expiry_date = Column(Date)  # Expiry date of the product, if applicable.
    discount_rate = Column(DECIMAL(10, 2))  # Discount rate applied to the product, if any.
    product_images_urls = Column(JSON)  # URLs to images of the product.
    product_logo_url = Column(String(255))  # URL to the product's logo.
    email_leads_recipients = Column(JSON)  # Email addresses to receive leads generated by the product.
    lead_recipient_channel = Column(SQLAlchemyEnum('Whatsapp', 'Email', 'CRM', 'Phone', name='lead_channels_options'))  # Preferred channel for receiving leads.
    lead_recipient_details = Column(JSON)  # Details about the lead reception channel.
    amenities = Column(JSON)  # Amenities included with the property.
    author_id = Column(Integer, ForeignKey('users.id'))  # Isso associa um produto a um usuário (autor).
    client_id = Column(Integer, ForeignKey('clients.id'))


    profit_analysis = relationship('ProductProfitAnalysis', back_populates='product')    
    plan_trafego_pago = relationship("PlanTrafegoPago", back_populates="product")

    __mapper_args__ = {
        'polymorphic_identity': 'product',
        'polymorphic_on': type
    }

    # Relationships:
    author = relationship("Users", back_populates="products", foreign_keys=[author_id])
    client = relationship("Client", back_populates="products")  # The client associated with the product.
    plan_trafego_pago = relationship("PlanTrafegoPago", back_populates="product")  # Traffic plans associated with the product.
    client = relationship("Client", back_populates="products")

    def __repr__(self):
        return f"<Product id={self.id}, name={self.product_name}, type={self.type}>"


# In your frontend with Streamlit, you can create logic that presents different input fields based on the value of lead_recipient_channel.
# For example, if the selected channel is "Whatsapp", you can prompt the user to enter the WhatsApp number.
# These details will then be stored in the lead_recipient_details field as JSON.

class RealEstateProduct(Product):
    """
    Represents a Real Estate Product, extending the general Product class to include specific fields relevant to real estate properties.
    This class uses SQLAlchemy's 'single table inheritance', meaning all real estate product attributes are stored in the 'products' table alongside the common Product attributes.
    """
    __mapper_args__ = {'polymorphic_identity': 'Imob'}  # SQLAlchemy inheritance configuration.

    status = Column(SQLAlchemyEnum('Pronto para morar', 'Na planta', 'Lançamento Breve', 'Em Construção', name='product_status_options'))  # Status of the real estate product.
    home_type = Column(SQLAlchemyEnum('Vertical', 'Casa', 'Condomínio Horizontal', name='home_types_options'))  # Type of home (apartment, house, etc.).
    number_bedrooms = Column(Integer)  # Number of bedrooms.
    area = Column(DECIMAL(10,2))  # Total area of the property in square meters.
    street_name = Column(String(255))  # Street name of the property's location.
    cep = Column(String(255))  # Postal code of the property's location.
    services_offered = Column(JSON, comment='List of services provided by the fitness center or gym.')  # Services offered by the gym.

    addr_neighbourhood = Column(String(255))  # Neighborhood of the property.
    door_number = Column(String)  # Door number of the property.
    city = Column(String(30))  # City where the property is located.
    bathrooms = Column(Integer)  # Number of bathrooms in the property.
    parking_spaces = Column(Integer)  # Number of parking spaces available.
    floor = Column(Integer)  # Floor number, applicable for apartments.
    building_name = Column(String(255))  # Name of the building or complex.
    construction_year = Column(Integer)  # Year when the property was constructed.
    condo_fee = Column(DECIMAL(10,2))  # Monthly condominium fee.
    iptu = Column(DECIMAL(10,2))  # Annual IPTU tax rate.

    def __repr__(self):
        return f"<RealEstateProduct(id={self.id}, name='{self.product_name}', type='Imob', status='{self.status}', home_type='{self.home_type}', city='{self.city}')>"

class Infoproduct(Product):
    """
    Represents an Infoproduct, a type of digital product typically used for educational or informational purposes.
    This class extends the general Product class with fields specifically relevant to infoproducts like online courses, e-books, etc.
    """
    __mapper_args__ = {'polymorphic_identity': 'Infoproduto'}  # SQLAlchemy inheritance configuration.

    infoproduct_host = Column(SQLAlchemyEnum('Hotmart', 'Eduzz', 'Monetizze', 'Udemy', 'Kajabi', name='infoproduct_hosts'), comment='Platform for hosting and selling the infoproduct.')  # Hosting platform for the infoproduct.
    market_niche = Column(SQLAlchemyEnum('Desenvolvimento Pessoal', 'Marketing Digital', 'Saúde e Bem-Estar', 'Negócios e Investimentos', 'Educação e Ensino', 'Relacionamentos', 'Artes e Entretenimento', 'Tecnologia e Programação', 'Moda e Beleza', 'Gastronomia e Culinária', name='market_niches'), comment='Target market or niche of the infoproduct.')  # Market niche for the infoproduct.
    access_type = Column(SQLAlchemyEnum('Vitalício', 'Limitado', 'Mensal', 'Anual', name='access_types'), comment='Type of access provided to the product (e.g., lifetime, limited).')  # Type of access for the infoproduct.
    course_level = Column(SQLAlchemyEnum('Iniciante', 'Intermediário', 'Avançado', name='course_levels'), comment='Intended level of audience (beginner, intermediate, advanced).')  # Level of the course offered.

    def __repr__(self):
        return f"<Infoproduct(id={self.id}, name='{self.product_name}', host='{self.infoproduct_host}', niche='{self.market_niche}')>"

class Academia(Product):
    """
    Represents a fitness or gym-related product, extending the general Product class.
    This can include memberships, classes, or other services offered by a fitness center or gym.
    """
    __mapper_args__ = {'polymorphic_identity': 'Academia'}  # SQLAlchemy inheritance configuration.

    location_features = Column(String, comment='Characteristics of the gym\'s location.')  # Features of the gym's location.
    membership_types = Column(JSON, comment='Types of gym memberships available.')  # Types of gym memberships.

    def __repr__(self):
        # String representation of the Academia instance.
        return f"<Academia(id={self.id}, name='{self.product_name}', services_offered={self.services_offered}, target_audience='{self.target_audience}', location_features='{self.location_features}')>"

class Clinica(Product):
    """
    Represents a clinical product or service, extending the general Product class.
    This can include various health services, treatments, or medical consultations offered by a clinic.
    """
    __mapper_args__ = {'polymorphic_identity': 'Clinica'}  # SQLAlchemy inheritance configuration.

    medical_specialties = Column(JSON, comment='List of medical specialties offered by the clinic.')  # Medical specialties.
    insurance_accepted = Column(JSON, comment='Health insurance policies accepted by the clinic.')  # Insurances accepted.
    certification_levels = Column(String, comment='Certification levels attained by the clinic.')  # Clinic certifications.

    def __repr__(self):

        return f"<Clinica(id={self.id}, name='{self.product_name}', specialties='{self.medical_specialties}')>"

class Varejo(Product):
    """
    Represents a retail product or service, extending the general Product class.
    This class is tailored for retail stores, including details such as product range,
    target market, store location, and store size.
    """
    __mapper_args__ = {'polymorphic_identity': 'Varejo'}  # SQLAlchemy inheritance configuration.

    product_ranges = Column(JSON, comment='Range of products offered by the retail store.')  # Product ranges.
    target_market = Column(String, comment='Target market for the retail store.')  # Target market.
    store_location = Column(String, comment='Physical location of the retail store.')  # Store location.
    store_size = Column(DECIMAL, comment='Size of the store in square meters.')  # Store size.

    def __repr__(self):
        return f"<Varejo(id={self.id}, name='{self.product_name}', market='{self.target_market}')>"

class ECommerce(Product):
    """
    Represents an e-commerce product or service, extending the general Product class.
    This class is tailored for e-commerce businesses, including details such as the platform used,
    payment methods, shipping options, and return policy.

    Attributes:
    - platform_used: The e-commerce platform used by the business (e.g., Shopify, WooCommerce).
    - payment_methods: A JSON list of payment methods available on the e-commerce site.
    - shipping_options: A JSON list of shipping options provided by the e-commerce business.
    - return_policy: The return policy defined by the e-commerce business.
    """
    __mapper_args__ = {'polymorphic_identity': 'E-commerce'}  # SQLAlchemy inheritance configuration.

    platform_used = Column(String, comment='E-commerce platform used by the business.')  # E-commerce platform.
    payment_methods = Column(JSON, comment='Payment methods available on the site.')  # Payment methods.
    shipping_options = Column(JSON, comment='Shipping options provided by the business.')  # Shipping options.
    return_policy = Column(String, comment='Return policy of the e-commerce business.')  # Return policy.

    def __repr__(self):
        # String representation of the ECommerce instance.
        return f"<ECommerce(id={self.id}, name='{self.product_name}', platform='{self.platform_used}')>"

class ObjectiveTrafegoPago(Base):
    __tablename__ = 'objectives_trafego_pago'
    
    id = Column(Integer, primary_key=True)
    briefing_id = Column(Integer, ForeignKey('briefing_trafego_pago.id'))
    goal_title = Column(String)
    current_amount = Column(DECIMAL)
    goal_amount = Column(DECIMAL)
    # Relacionamento com o briefing
    briefing = relationship("BriefingTrafegoPago", back_populates="objectives")
    # Relacionamento com as ações estratégicas
    strategic_actions = relationship("StrategicActionsTrafegoPago", back_populates="objective")

class BriefingTrafegoPago(Base):
    __tablename__ = 'briefing_trafego_pago'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    last_updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    objectives = Column(Text)
    target_audience = Column(Text)
    budget = Column(DECIMAL)
    platforms = Column(Text)
    key_messages = Column(Text)
    expected_results = Column(Text)
    
    objectives = relationship('ObjectiveTrafegoPago', back_populates='briefing')
    plan_trafego_pago = relationship('PlanTrafegoPago', back_populates='briefing')
    client = relationship("Client", back_populates="briefing_trafego_pago")
    author = relationship("Users", back_populates="briefings_trafego_pago", foreign_keys=[author_id])
    updater = relationship( "Users", back_populates="updated_briefings_trafego_pago",foreign_keys=[last_updated_by])

class PlanTrafegoPago(Base):
    __tablename__ = 'plans_trafego_pago'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    briefing_id = Column(Integer, ForeignKey('briefing_trafego_pago.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    context = Column(Text)
    strategy_summary = Column(Text)
    monthly_budget = Column(Float)
    plan_name = Column(String(255))
    product_id = Column(Integer, ForeignKey('products.id'))
    strategic_actions = relationship('StrategicActionsTrafegoPago', back_populates='plan')

    client = relationship("Client", back_populates="plans_trafego_pago")
    briefing = relationship("BriefingTrafegoPago", back_populates="plan_trafego_pago")
    product = relationship("Product", back_populates="plan_trafego_pago")
    author = relationship("Users", back_populates="created_plans_trafego_pago")

class MetaAdsObjective(Base):
    __tablename__ = 'meta_ads_objectives'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    friendly_name = Column(String, unique=True)
    description = Column(Text)

    
    optimizations = relationship("ObjectiveOptimization", back_populates="objective")
    strategic_actions = relationship("StrategicActionsTrafegoPago", back_populates="objective_meta_ads")

class ObjectiveOptimization(Base):
    __tablename__ = 'objective_optimizations'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    friendly_name = Column(String, unique=True)
    objective_id = Column(Integer, ForeignKey('meta_ads_objectives.id'))
    objective = relationship("MetaAdsObjective", back_populates="optimizations")

    strategic_actions = relationship("StrategicActionsTrafegoPago", back_populates="optimization")

class StrategicActionsTrafegoPago(Base):
    __tablename__ = 'strategic_actions_trafego_pago'
    
    id = Column(Integer, primary_key=True)
    objective_id = Column(Integer, ForeignKey('meta_ads_objectives.id'))
    optimization_id = Column(Integer, ForeignKey('objective_optimizations.id'))
    plan_id = Column(Integer, ForeignKey('plans_trafego_pago.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    action_name = Column(String(255))
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    monthly_budget = Column(Float)
    platform = Column(Text)  # Assumindo que 'platforms' foi definido em outro lugar
    min_cost_per_result_expected = Column(Float)
    max_cost_per_result_expected = Column(Float)
    call_to_action = Column(Text)  # Assumindo que 'meta_ads_call_to_actions' foi definido em outro lugar
    objective_meta_ads_id = Column(Integer, ForeignKey('meta_ads_objectives.id'))

    budgets = relationship('ActionBudgets', back_populates='action')
    # Adicione o campo para o objetivo relacionado
    objective_id = Column(Integer, ForeignKey('objectives_trafego_pago.id'))
    # Relacionamento com Objective
    objective = relationship("ObjectiveTrafegoPago", back_populates="strategic_actions")
    objective_meta_ads = relationship("MetaAdsObjective", back_populates="strategic_actions")


    optimization = relationship("ObjectiveOptimization", back_populates="strategic_actions")
    plan = relationship("PlanTrafegoPago", back_populates="strategic_actions")
    client = relationship("Client", back_populates="strategic_actions")

class ActionBudgets(Base):
    __tablename__ = 'action_budgets'
    
    id = Column(Integer, primary_key=True)
    action_id = Column(Integer, ForeignKey('strategic_actions_trafego_pago.id'))
    month_year = Column(Date)
    budget = Column(Float)
    action = relationship("StrategicActionsTrafegoPago", back_populates="budgets")
   
    def __repr__(self):
        return f"<ActionBudget id={self.id}, action_id={self.action_id}, month_year={self.month_year}, budget={self.budget}>"

class ProductProfitAnalysis(Base):
    __tablename__ = 'product_profit_analysis'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    spend_level = Column(Float)
    attributed_revenue = Column(Float)
    input_costs = Column(Float)
    gross_profit = Column(Float)
    taxes = Column(Float)
    shipping_fees = Column(Float)
    operational_cost = Column(Float)
    digital_ad_spend = Column(Float)
    roas = Column(Float)
    net_profit = Column(Float)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    product = relationship("Product", back_populates="profit_analysis")
    client = relationship("Client", back_populates="profit_analysis")

    def __repr__(self):
        return f"<ProductProfitAnalysis id={self.id}, product_id={self.product_id}, net_profit={self.net_profit}>"    

class ActionPlanAssessoria(Base):
    __tablename__ = 'action_plan_assessoria'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    start_date = Column(Date)
    what = Column(Text)
    why = Column(Text)
    how = Column(Text)
    notes = Column(Text)
    status = Column(SQLAlchemyEnum("Aguardando início", "Em Andamento", "Em Criação", "Em Orçamento", "Em Aprovação", "Reprovado", "Aprovado", "Em Execução", "Concluído", "Cancelado", "Stand By", name="action_plan_assessoria_status"))
    responsible_id = Column(Integer)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<ActionPlanAssessoria(id={self.id}, client_id={self.client_id}, author_id={self.author_id})>"

class CategoryEnumCreative(str, Enum):
    CRIACAO = 'Criação'
    ADAPTACAO = 'Adaptação'
    

class CategoryEnumRedesSociais(str, Enum):
    REELS = 'Reels'
    STORIES = 'Stories'
    CARDS = 'Cards'
    STORIES_REPOST = 'Stories Repost'
    CONTENT = 'Conteúdo'


class DeliveryControlCreative(Base):
    __tablename__ = 'delivery_control_creative'

    id = Column(Integer, primary_key=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    updated_by = relationship("Users", foreign_keys=[updated_by_id])
    client_id = Column(Integer, ForeignKey('clients.id'))
    client = relationship("Client", back_populates="delivery_control_creative")
    job_link = Column(String)
    project = Column(String)
    category= Column(SQLAlchemyEnum(CategoryEnumCreative))
    job_title = Column(String)
    used_creative_mandalecas = Column(Integer, default=0)
    used_format_adaptation_mandalecas = Column(Integer, default=0)
    used_content_mandalecas = Column(Integer, default=0)
    job_creation_date = Column(Date)
    job_start_date = Column(Date)
    job_deadline_date = Column(Date)
    job_finish_date = Column(Date)
    job_status = Column(String)
    user_in_charge_id = Column(Integer, ForeignKey('users.id'))
    user_in_charge = relationship("Users", foreign_keys=[user_in_charge_id], back_populates="user_in_charge_jobs")
    requested_by_id = Column(Integer, ForeignKey('users.id'))
    requested_by = relationship("Users", foreign_keys=[requested_by_id], back_populates="requested_jobs")

    client = relationship("Client", back_populates="delivery_control_creatives")
    user_in_charge = relationship("Users", foreign_keys=[user_in_charge_id], back_populates="user_in_charge_jobs")
    requested_by = relationship("Users", foreign_keys=[requested_by_id], back_populates="requested_jobs")

def __repr__(self):
    return f"job='{self.job_title}', category='{self.category}')>"

class DeliveryControlAssessoria(Base):
    __tablename__ = 'delivery_control_assessoria'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.now)
    service_id = Column(Integer)
    action_date = Column(Date)
    plan_id = Column(Integer, ForeignKey('action_plan_assessoria.id'))
    task = Column(Text)
    notes = Column(Text)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<DeliveryControlAssessoria(id={self.id}, client_id={self.client_id}, plan_id={self.plan_id})>"

class DeliveryControlRedesSociais(Base):
    __tablename__ = 'delivery_control_redes_social'

    id = Column(Integer, primary_key=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    updated_by = relationship("Users", foreign_keys=[updated_by_id])
    client_id = Column(Integer, ForeignKey('clients.id'))
    client = relationship("Client", back_populates="delivery_control_creative")
    job_link = Column(String)
    project = Column(String)
    category= Column(SQLAlchemyEnum(CategoryEnumRedesSociais))
    job_title = Column(String)
    used_creative_mandalecas = Column(Integer, default=0)
    used_format_adaptation_mandalecas = Column(Integer, default=0)
    used_content_mandalecas = Column(Integer, default=0)
    job_creation_date = Column(Date)
    job_deadline_date = Column(Date)
    job_start_date = Column(Date)
    job_deadline_met = Column(Boolean)
    job_finish_date = Column(Date)
    job_status = Column(String)
    user_in_charge_id = Column(Integer, ForeignKey('users.id'))
    user_in_charge = relationship("Users", foreign_keys=[user_in_charge_id], back_populates="user_in_charge_jobs")
    requested_by_id = Column(Integer, ForeignKey('users.id'))
    requested_by = relationship("Users", foreign_keys=[requested_by_id], back_populates="requested_jobs")
    client = relationship("Client", back_populates="delivery_control_redes_sociais")
    user_in_charge = relationship("Users", foreign_keys=[user_in_charge_id], back_populates="user_in_charge_redes_sociais")
    requested_by = relationship("Users", foreign_keys=[requested_by_id], back_populates="requested_redes_sociais")

class DeliveryControlTrafegoPago(Base):

    __tablename__ = 'controle_entregas_trafego_pago'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.now)
    meta_ads_spend = Column(Float)
    google_ads_spend = Column(Float)
    meta_ads_remaining_balance = Column(Float)
    google_ads_remaining_balance = Column(Float)
    plan_id = Column(Integer, ForeignKey('plans_trafego_pago.id'))
    sent_guidance = Column(Boolean)
    sent_plan = Column(Boolean)
    notes = Column(Text)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<DeliveryControlTrafegoPago(id={self.id}, client_id={self.client_id}, plan_id={self.plan_id})>"

  
    # Configurando a conexão com o banco de dados


    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"
    
    
    if __name__ == "__main__":
        init_db()
