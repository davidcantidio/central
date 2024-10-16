from sqlalchemy import create_engine, DateTime, Column, DECIMAL, Integer, String, Boolean, ForeignKey, TIMESTAMP, Numeric, CheckConstraint, JSON, Date, Text, Float, Table, Index, event, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from sqlalchemy.orm import relationship, sessionmaker
from enum import Enum
from sqlalchemy.types import Enum as SQLAlchemyEnum
from sqlalchemy.orm import declarative_base  # Importando a nova função


Base = declarative_base()  # Usando a nova função


# Configurando a conexão com o banco de dados
DATABASE_URL = "sqlite:///./test.db"  # Substitua pelo URL do seu banco de dados

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criando todas as tabelas
Base.metadata.create_all(bind=engine)

# Agora você pode criar uma sessão e realizar operações no banco de dados
db = SessionLocal()


#Enums

class JobCategoryEnum(str, Enum):
    STORIES_REPOST_INSTAGRAM = 'Stories Repost Instagram'
    FEED_INSTAGRAM = 'Feed Instagram'
    FEED_TIKTOK = 'Feed Tiktok'
    FEED_LINKEDIN = 'Feed Linkedin'
    STORIES_INSTAGRAM = 'Stories Instagram'
    CONTENT_PRODUCTION = 'Produção de Conteúdo'
    CRIACAO = 'Criação'
    ADAPTACAO = 'Adaptação'
    STATIC_TRAFEGO_PAGO = 'Tráfego Pago Estático'
    ANIMATED_TRAFEGO_PAGO = 'Tráfego Pago Animado'
    CARD_INSTAGRAM = 'Card Instagram'
    CAROUSEL_INSTAGRAM = 'Carrossel Instagram'
    REELS_INSTAGRAM = 'Reels Instagram'

class RedesSociaisPlanStatusEnum(str, Enum):
    AWAITING = 'Aguardando'
    DELAYED = 'Atrasado'
    ON_TIME = 'No prazo'


class DeliveryCategoryEnum(str, Enum):
    CRIACAO = "Criação"
    REDES_SOCIAIS = "Redes Sociais"
    TRAFEGO_PAGO = "Tráfego Pago"
    CONTENT_PRODUCTION = 'Produção de Conteúdo'

def map_category_to_delivery_category(job_category):
    mapping = {
        JobCategoryEnum.CRIACAO: DeliveryCategoryEnum.CRIACAO,
        JobCategoryEnum.ADAPTACAO: DeliveryCategoryEnum.CRIACAO,
        JobCategoryEnum.CONTENT_PRODUCTION: DeliveryCategoryEnum.CONTENT_PRODUCTION,
        JobCategoryEnum.STORIES_INSTAGRAM: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.FEED_LINKEDIN: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.FEED_TIKTOK: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.STORIES_REPOST_INSTAGRAM: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.FEED_INSTAGRAM: DeliveryCategoryEnum.REDES_SOCIAIS,
        JobCategoryEnum.STATIC_TRAFEGO_PAGO: DeliveryCategoryEnum.TRAFEGO_PAGO,
        JobCategoryEnum.ANIMATED_TRAFEGO_PAGO: DeliveryCategoryEnum.TRAFEGO_PAGO
    }
    return mapping.get(job_category)




# Tabelas associativas
role_department_association = Table(
    'role_department', Base.metadata,
    Column('department_id', Integer, ForeignKey('departments.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

client_liaison_association = Table(
    'client_liaison_association', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id')),
    Column('liaison_id', Integer, ForeignKey('liaisons.id'))
)

client_account_executives_association = Table(
    'client_account_executives', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

client_social_media_association = Table(
    'client_social_media', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

client_copywriter_association = Table(
    'client_copywriter', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

client_services_association = Table(
    'client_services', Base.metadata,
    Column('client_id', Integer, ForeignKey('clients.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True)
)

# Enums
class ContractTypes(str, Enum):
    POR_JOB = "Por job"
    POR_MES = "Por mês"
    POR_JORNADA = "Por jornada"




# Definições das classes
class MetaAdsCTA(Base):
    __tablename__ = 'meta_ads_ctas'
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    name = Column(String, nullable=False, unique=True)
    friendly_name = Column(String, nullable=False)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    friendly_name = Column(String, nullable=False)
    departments = relationship("Department", secondary=role_department_association, back_populates="roles")
    employees = relationship("Users", back_populates="role")
    role_scopes = relationship("RoleDepartmentScope", back_populates="role")

    def __repr__(self):
        return f"Role(id={self.id}, name='{self.name}', employees_count={len(self.employees)})"

class RoleDepartmentScope(Base):
    __tablename__ = 'role_department_scopes'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), primary_key=True)
    activity_scopes = Column(JSON)
    role = relationship("Role", back_populates="role_scopes")
    department = relationship("Department", back_populates="department_scopes")

    def __repr__(self):
        return f"<RoleDepartmentScope(role_id={self.role_id}, department_id={self.department_id}, activity_scopes={self.activity_scopes})>"

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    name = Column(String(255), unique=True, nullable=False)
    employees = relationship("Users", back_populates="department", foreign_keys="[Users.department_id]")
    roles = relationship("Role", secondary=role_department_association, back_populates="departments")
    department_scopes = relationship("RoleDepartmentScope", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"

class EmployeeContract(Base):
    __tablename__ = 'employee_contract'
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('users.id'))
    type = Column(SQLAlchemyEnum(ContractTypes), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    active = Column(Boolean, default=True)
    employee = relationship("Users", back_populates="employee_contracts")

    def __repr__(self):
        return f"<EmployeeContract(id={self.id}, type='{self.type}', active={self.active}, employee_id={self.employee_id})>"

class Users(Base):
    __tablename__ = 'users'

    # Definição das colunas...
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
    employee_contracts = relationship("EmployeeContract", back_populates="employee", cascade="all, delete, delete-orphan")
    role = relationship("Role", back_populates="employees")
    reports = relationship("Report", back_populates="author")
    briefing_redes_sociais = relationship("BriefingRedesSociais", back_populates="author", foreign_keys="[BriefingRedesSociais.author_id]")
    products = relationship("Product", back_populates="author")
    briefings_trafego_pago = relationship("BriefingTrafegoPago", foreign_keys="[BriefingTrafegoPago.author_id]")
    briefing_redes_sociais_updates = relationship("BriefingRedesSociais", back_populates="updater", foreign_keys="[BriefingRedesSociais.last_updated_by]")
    updated_briefings_trafego_pago = relationship("BriefingTrafegoPago", back_populates="updater", foreign_keys="[BriefingTrafegoPago.last_updated_by]")
    created_plans_trafego_pago = relationship("PlanTrafegoPago", back_populates="author")
    delivery_controls_in_charge = relationship("DeliveryControl", back_populates="user_in_charge", foreign_keys="[DeliveryControl.user_in_charge_id]")
    delivery_controls_requested = relationship("DeliveryControl", back_populates="requested_by", foreign_keys="[DeliveryControl.requested_by_id]")
    authored_action_plans_assessoria = relationship("ActionPlanAssessoria", back_populates="author")
    authored_plans_redes_sociais = relationship("RedesSociaisPlan", back_populates="author")

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
    position = Column(String(255))
    title = Column(SQLAlchemyEnum('Legal Representative', 'Financial Representative', 'Other', name='liaison_titles', nullable=False))
    legal_representative = Column(Boolean)
    finances_representative = Column(Boolean)
    clients = relationship("Client", secondary=client_liaison_association, back_populates="liaisons")

class Client(Base):
    __tablename__ = 'clients'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    business_type = Column(SQLAlchemyEnum('Imob', 'Academia', 'Clínica', 'Político'), index=True)
    cnpj = Column(String(18), unique=True)
    cpf = Column(String(11), unique=True)
    aliases = Column(JSON)
    monthly_plan_deadline_day = Column(Integer, default=20)
    monthly_redes_guidance_deadline_day = Column(Integer, default=10)
    is_instagram_connected_facebook_page = Column(Boolean, default=False)
    is_active_impulsionamento_instagram = Column(Boolean, default=False)
    is_active_impulsionamento_linkedin = Column(Boolean, default=False)
    is_active_impulsionamento_tiktok = Column(Boolean, default=False)
    impulsionamento_budget = Column(Float, default=0)
    is_active_redes_instagram = Column(Boolean, default=False)
    is_active_redes_linkedin = Column(Boolean, default=False)
    is_active_impulsionamento_linkedin = Column(Boolean, default=False)
    is_active_tiktok = Column(Boolean, default=False)
    is_active_google_ads = Column(Boolean, default=False)
    is_active_trafego_pago = Column(Boolean, default=False)
    is_active_tiktok_ads = Column(Boolean, default=False)
    is_active_linkedin_ads = Column(Boolean, default=False)
    is_active_redes_tiktok = Column(Boolean, default=False)
    invoice_recipients_emails = Column(JSON)
    foundation_date = Column(Date)
    due_charge_date = Column(Date)
    legal_name = Column(Text)
    logo_url = Column(String(255))
    n_monthly_contracted_creative_mandalecas = Column(Float, default=0)
    n_monthly_contracted_format_adaptation_mandalecas = Column(Float, default=0)
    n_monthly_contracted_content_production_mandalecas = Column(Float, default=0)
    n_monthly_contracted_stories_instagram_mandalecas = Column(Float, default=0)
    n_monthly_contracted_feed_linkedin_mandalecas = Column(Float, default=0)
    n_monthly_contracted_feed_tiktok_mandalecas = Column(Float, default=0)
    

    n_monthly_contracted_stories_repost_instagram_mandalecas = Column(Float, default=0)
    n_monthly_contracted_feed_instagram_mandalecas = Column(Float, default=0)
    n_monthly_contracted_trafego_pago_static =  Column(Float, default=0)
    n_monthly_contracted_trafego_pago_animated =  Column(Float, default=0)
    n_monthly_contracted_blog_text_mandalecas = Column(Float, default=0)
    n_monthly_contracted_website_maintenance_mandalecas = Column(Float, default=0)
    accumulated_blog_text_mandalecas = Column(Float, default=0)
    accumulated_website_maintenance_mandalecas = Column(Float, default=0)
    accumulated_trafego_pago_static =  Column(Float, default=0)
    accumulated_trafego_pago_animated =  Column(Float, default=0)
    accumulated_creative_mandalecas = Column(Float, default=0)
    accumulated_format_adaptation_mandalecas = Column(Float, default=0)
    accumulated_content_production_mandalecas = Column(Float, default=0)
    accumulated_feed_linkedin_mandalecas = Column(Float, default=0)
    accumulated_feed_tiktok_mandalecas = Column(Float, default=0)
    
    accumulated_stories_instagram_mandalecas = Column(Float, default=0)
    accumulated_stories_repost_instagram_mandalecas = Column(Float, default=0)
    accumulated_feed_instagram_mandalecas = Column(Float, default=0)
    name = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    date_start_communication_plan = Column(Date)
    date_end_communication_plan = Column(Date)
    date_presentation_communication_plan = Column(Date)
    postal_code = Column(String(10))
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
    hashtags = Column(JSON)
    address = Column(String(255))
    address_number = Column(String(10))
    address_complement = Column(String(255))
    address_neighbourhood = Column(String(255))
    city = Column(String(255))
    state = Column(String(2))
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
    delivery_controls = relationship("DeliveryControl", back_populates="client")
    account_executives = relationship("Users", secondary=client_account_executives_association)
    social_media = relationship("Users", secondary=client_social_media_association)
    copywriter = relationship("Users", secondary=client_copywriter_association)
    action_plans_assessoria = relationship("ActionPlanAssessoria", back_populates="client")
    plans_redes_sociais = relationship("RedesSociaisPlan", back_populates="client")
    content_productions = relationship("ContentProduction", back_populates="client")
    attention_points = relationship('AttentionPoints', back_populates='client', cascade='all, delete-orphan')
    manutencao_site = relationship('WebsiteMaintenance', back_populates='client', cascade='all, delete-orphan')
    texto_blog = relationship('BlogText', back_populates='client', cascade='all, delete-orphan')
    meetings = relationship('Meetings', back_populates='client')
    plannings_delivered_copy = relationship('PlanningDeliveredCopy', back_populates='client')
    marketing_planning_reviews = relationship('MarketingPlanningReview', back_populates='client')

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', business_type='{self.business_type}')>"

class GoogleAdsInsights(Base):
    __tablename__ = 'google_ads_insights'
    id = Column(Integer, primary_key=True)
    google_ads_profile_id = Column(String(60), ForeignKey('google_ads_profiles.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    insights_data = Column(JSON)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    profile = relationship("GoogleAdsProfile", back_populates="insights")
    client = relationship("Client", back_populates="google_ads_insights")

    def __repr__(self):
        return f"<GoogleAdsInsights(id={self.id})>"

class OperandProject(Base):
    __tablename__ = 'operand_projects'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    id_project_operand = Column(String(255), nullable=False, unique=True)
    url_project_operand = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    client = relationship("Client", back_populates="operand_projects", foreign_keys=[client_id])

    def __repr__(self):
        return f"<OperandProject(id={self.id}, name='{self.name}', client_id={self.client_id})>"

class ServiceItem(Base):
    __tablename__ = 'service_items'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price_tokens = Column(Float, CheckConstraint('price_tokens >= 0'), nullable=False)
    price_reals = Column(Float, CheckConstraint('price_reals >= 0'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    service = relationship("Service", back_populates="service_items")
    client = relationship("Client", back_populates="service_items")

    def __repr__(self):
        return f"<ServiceItem(id={self.id}, name='{self.name}', price_tokens={self.price_tokens}, price_reals={self.price_reals})>"

class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    name = Column(String(90), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon_html_code = Column(String(255))
    clients = relationship("Client", secondary=client_services_association, back_populates="services")
    service_items = relationship("ServiceItem", back_populates="service")

    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}')>"

class InstagramInsights(Base):
    __tablename__ = 'instagram_insights'
    id = Column(Integer, primary_key=True)
    instagram_profile_id = Column(String(60), ForeignKey('instagram_profiles.id'), nullable=False)
    insights_data = Column(JSON)
    insight_type = Column(SQLAlchemyEnum('BusiestHours', 'Demographic', 'Media', 'User'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    instagram_profile = relationship("InstagramProfile", back_populates="insights")

class InstagramProfile(Base):
    __tablename__ = 'instagram_profiles'
    id = Column(String(60), primary_key=True)
    username = Column(String(40), nullable=False)
    official_hashtags = Column(JSON)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    insights = relationship("InstagramInsights", back_populates="instagram_profile")
    client = relationship("Client", back_populates="instagram_profile")

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
    insights = relationship("LinkedinInsights", back_populates="linkedin_profile")

class GoogleAdsProfile(Base):
    __tablename__ = 'google_ads_profiles'
    id = Column(String(60), primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    insights = relationship("GoogleAdsInsights", back_populates="profile")
    client = relationship("Client", back_populates="google_ads_profiles")

class LinkedinInsights(Base):
    __tablename__ = 'linkedin_insights'
    id = Column(Integer, primary_key=True)
    linkedin_profile_id = Column(String(60), ForeignKey('linkedin_profiles.id'))
    insights_data = Column(JSON)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    client_id = Column(Integer, ForeignKey('clients.id'))
    linkedin_profile = relationship("LinkedinProfile", back_populates="insights")
    client = relationship("Client", back_populates="linkedin_insights")

    def __repr__(self):
        return f"<LinkedinInsights(id={self.id}, profile='{self.linkedin_profile.user_name}')>"

class TikTokProfile(Base):
    __tablename__ = 'tiktok_profiles'
    id = Column(String(60), primary_key=True)
    username = Column(String(40), nullable=False)
    biography = Column(Text)
    followers_count = Column(Integer)
    following_count = Column(Integer)
    likes_count = Column(Integer)
    video_count = Column(Integer)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    client = relationship("Client", back_populates="tiktok_profile")
    tiktok_insights = relationship("TikTokInsights", back_populates="tiktok_profile")

    def __repr__(self):
        return f"<TikTokProfile(id='{self.id}', username='{self.username}')>"

class TikTokInsights(Base):
    __tablename__ = 'tiktok_insights'
    id = Column(Integer, primary_key=True)
    tiktok_profile_id = Column(String(60), ForeignKey('tiktok_profiles.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    insights_data = Column(JSON)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    tiktok_profile = relationship("TikTokProfile", back_populates="tiktok_insights")
    client = relationship("Client", back_populates="tiktok_insights")

    def __repr__(self):
        return f"<TikTokInsights(id={self.id}, start_date='{self.start_date}', end_date='{self.end_date}')>"

class MetaAdsAssets(Base):
    __tablename__ = 'meta_ads_assets'
    id = Column(Integer, primary_key=True)
    id_business_manager = Column(Integer, unique=True)
    pixel_id = Column(String(255), unique=True)
    offline_conversions_id = Column(String(255), unique=True)
    conversion_api_token = Column(String(255))
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    client = relationship("Client", back_populates="meta_ads_assets")
    facebook_pages = relationship("FacebookPage", back_populates="meta_ads_asset")
    meta_ads_accounts = relationship("MetaAdsAccount", back_populates="meta_ads_asset")
    product_catalogs = relationship("MetaAdsProductCatalog", back_populates="meta_ads_asset")

    def __repr__(self):
        return f"<MetaAdsAssets(id_business_manager={self.id_business_manager}, pixel_id='{self.pixel_id}')>"

class FacebookPage(Base):
    __tablename__ = 'facebook_pages'
    id = Column(String(255), primary_key=True)
    meta_ads_asset_id = Column(Integer, ForeignKey('meta_ads_assets.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    meta_ads_asset = relationship("MetaAdsAssets", back_populates="facebook_pages")
    client = relationship("Client", back_populates="facebook_pages")

    def __repr__(self):
        return f"<FacebookPage(id='{self.id}', client_id={self.client_id})>"

class MetaAdsAccount(Base):
    __tablename__ = 'meta_ads_accounts'
    id = Column(String(255), primary_key=True)
    meta_ads_asset_id = Column(Integer, ForeignKey('meta_ads_assets.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    meta_ads_asset = relationship("MetaAdsAssets", back_populates="meta_ads_accounts")
    client = relationship("Client", back_populates="meta_ads_accounts")
    meta_ads_insights = relationship("MetaAdsInsights", back_populates="meta_ads_account")

    def __repr__(self):
        return f"<MetaAdsAccount(id='{self.id}', client_id={self.client_id})>"

class MetaAdsProductCatalog(Base):
    __tablename__ = 'meta_ads_product_catalogs'
    id = Column(String(255), primary_key=True)
    catalog = Column(JSON)
    meta_ads_asset_id = Column(Integer, ForeignKey('meta_ads_assets.id'), nullable=False)
    meta_ads_asset = relationship("MetaAdsAssets", back_populates="product_catalogs")

    def __repr__(self):
        return f"<MetaAdsProductCatalog(id='{self.id}', meta_ads_asset_id={self.meta_ads_asset_id})>"

class MetaAdsInsights(Base):
    __tablename__ = 'meta_ads_insights'
    id = Column(Integer, primary_key=True)
    insights_data = Column(JSON)
    updated_at = Column(TIMESTAMP, default=datetime.now, nullable=False)
    meta_ads_account_id = Column(String(255), ForeignKey('meta_ads_accounts.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    meta_ads_account = relationship("MetaAdsAccount", back_populates="meta_ads_insights")
    client = relationship("Client", back_populates="meta_ads_insights")

    def __repr__(self):
        return f"<MetaAdsInsights(id={self.id}, meta_ads_account_id='{self.meta_ads_account_id}', client_id={self.client_id})>"

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    date_start = Column(Date)
    date_end = Column(Date)
    title = Column(SQLAlchemyEnum('Assessoria de Marketing', 'Redes Sociais', 'Tráfego Pago', 'Criação', name='report_titles'))
    analysis = Column(Text)
    details = Column(JSON)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    client = relationship("Client", back_populates="reports")
    author = relationship("Users", back_populates="reports")

    def __repr__(self):
        return f"Relatório: {self.client}, {self.title} - {self.start_date} a {self.end_date}"

class BriefingRedesSociais(Base):
    __tablename__ = 'briefings_redes_sociais'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    last_updated_by = Column(Integer, ForeignKey('users.id'))
    target_audience_social_media = Column(Text)
    main_social_media_objective = Column(Text)
    main_content_type_social_media = Column(Text)
    how_followers_should_view_company = Column(Text)
    brand_personality = Column(Text)
    language_tone = Column(SQLAlchemyEnum('Formal', 'Técnica', 'Informal', 'Descolada', 'Gíria/Regionalismo', 'Pessoal', 'Impessoal', name='language_tones'))
    social_media_references = Column(Text)
    suggested_research_sources = Column(Text)
    instagram_login = Column(Text)
    instagram_password = Column(Text)
    free_space = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    is_ready = Column(Boolean)
    client = relationship("Client", back_populates="briefing_redes_sociais")
    author = relationship("Users", back_populates="briefing_redes_sociais", foreign_keys=[author_id])
    updater = relationship("Users", back_populates="briefing_redes_sociais_updates", foreign_keys=[last_updated_by])
    plans_redes_sociais = relationship("RedesSociaisPlan", back_populates="briefing", foreign_keys="[RedesSociaisPlan.briefing_id]")  # Adicionado relacionamento

class ContentProduction(Base):
    __tablename__ = 'producao_conteudo'
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # Chave primária
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    date = Column(TIMESTAMP)
    subject = Column(Text)
    notes = Column(Text)

    client = relationship("Client", back_populates="content_productions")


class RedesSociaisGuidance(Base):
    __tablename__ = 'direcionamento_redes_sociais'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    briefing_id = Column(Integer, ForeignKey('briefings_redes_sociais.id'))  # Adicionando a chave estrangeira aqui
    updated_at = Column(TIMESTAMP, default=datetime.now)
    status = Column(SQLAlchemyEnum(RedesSociaisPlanStatusEnum), nullable=False)
    responsible_id = Column(Integer)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    send_date = Column(TIMESTAMP)
    plan_status = Column(SQLAlchemyEnum(RedesSociaisPlanStatusEnum), nullable=False)

    __table_args__ = (
        UniqueConstraint('client_id', 'send_date', name='uix_guidance_client_id_send_date'),
        Index('ix_guidance_client_id_send_date', 'client_id', 'send_date')  # Novo nome do índice
    )

class RedesSociaisPlan(Base):
    __tablename__ = 'plano_redes_sociais'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    briefing_id = Column(Integer, ForeignKey('briefings_redes_sociais.id'))  # Adicionando a chave estrangeira aqui
    updated_at = Column(TIMESTAMP, default=datetime.now)
    status = Column(SQLAlchemyEnum(RedesSociaisPlanStatusEnum), nullable=False)
    responsible_id = Column(Integer)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    send_date = Column(TIMESTAMP)
    plan_status = Column(SQLAlchemyEnum(RedesSociaisPlanStatusEnum), nullable=False)

    __table_args__ = (
        UniqueConstraint('client_id', 'send_date', name='uix_1'),
        Index('ix_client_id_send_date', 'client_id', 'send_date')
    )

    # Relacionamentos
    client = relationship("Client", back_populates="plans_redes_sociais")
    author = relationship("Users", back_populates="authored_plans_redes_sociais")
    briefing = relationship("BriefingRedesSociais", back_populates="plans_redes_sociais")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    type = Column(SQLAlchemyEnum('Imob', 'Infoproduto', 'Academia', 'Clínica', 'Varejo', 'E-commerce', name='product_types'))
    product_name = Column(String(255))
    description = Column(Text)
    target_audience = Column(Text)
    differentials = Column(JSON)
    objections = Column(JSON)
    price = Column(DECIMAL(10, 2))
    is_membership = Column(Boolean)
    avg_ticket = Column(DECIMAL(10, 2))
    avg_insume_cost_per_product = Column(DECIMAL(10, 2))
    credit_card_fees = Column(DECIMAL(10, 2))
    fulfilment_cost_per_unit = Column(DECIMAL(10, 2))
    total_cost_of_product = Column(DECIMAL(10, 2))
    percentage_cost = Column(DECIMAL(10, 2))
    landing_page = Column(String(255))
    inventory_count = Column(Integer)
    supplier_id = Column(Integer)
    warranty_period = Column(String(255))
    return_policy_url = Column(String(255))
    manufacturing_date = Column(Date)
    expiry_date = Column(Date)
    discount_rate = Column(DECIMAL(10, 2))
    product_images_urls = Column(JSON)
    product_logo_url = Column(String(255))
    email_leads_recipients = Column(JSON)
    lead_recipient_channel = Column(SQLAlchemyEnum('Whatsapp', 'Email', 'CRM', 'Phone', name='lead_channels_options'))
    lead_recipient_details = Column(JSON)
    amenities = Column(JSON)
    author_id = Column(Integer, ForeignKey('users.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    profit_analysis = relationship('ProductProfitAnalysis', back_populates='product')
    plan_trafego_pago = relationship("PlanTrafegoPago", back_populates="product")
    __mapper_args__ = {
        'polymorphic_identity': 'product',
        'polymorphic_on': type
    }
    author = relationship("Users", back_populates="products", foreign_keys=[author_id])
    client = relationship("Client", back_populates="products")
    plan_trafego_pago = relationship("PlanTrafegoPago", back_populates="product")

    def __repr__(self):
        return f"<Product id={self.id}, name={self.product_name}, type={self.type}>"

class RealEstateProduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'Imob'}
    status = Column(SQLAlchemyEnum('Pronto para morar', 'Na planta', 'Lançamento Breve', 'Em Construção', name='product_status_options'))
    home_type = Column(SQLAlchemyEnum('Vertical', 'Casa', 'Condomínio Horizontal', name='home_types_options'))
    number_bedrooms = Column(Integer)
    area = Column(DECIMAL(10,2))
    street_name = Column(String(255))
    cep = Column(String(255))
    services_offered = Column(JSON, comment='List of services provided by the fitness center or gym.')
    addr_neighbourhood = Column(String(255))
    door_number = Column(String)
    city = Column(String(30))
    bathrooms = Column(Integer)
    parking_spaces = Column(Integer)
    floor = Column(Integer)
    building_name = Column(String(255))
    construction_year = Column(Integer)
    condo_fee = Column(DECIMAL(10,2))
    iptu = Column(DECIMAL(10,2))

    def __repr__(self):
        return f"<RealEstateProduct(id={self.id}, name='{self.product_name}', type='Imob', status='{self.status}', home_type='{self.home_type}', city='{self.city}')>"

class Infoproduct(Product):
    __mapper_args__ = {'polymorphic_identity': 'Infoproduto'}
    infoproduct_host = Column(SQLAlchemyEnum('Hotmart', 'Eduzz', 'Monetizze', 'Udemy', 'Kajabi', name='infoproduct_hosts'))
    market_niche = Column(SQLAlchemyEnum('Desenvolvimento Pessoal', 'Marketing Digital', 'Saúde e Bem-Estar', 'Negócios e Investimentos', 'Educação e Ensino', 'Relacionamentos', 'Artes e Entretenimento', 'Tecnologia e Programação', 'Moda e Beleza', 'Gastronomia e Culinária', name='market_niches'))
    access_type = Column(SQLAlchemyEnum('Vitalício', 'Limitado', 'Mensal', 'Anual', name='access_types'))
    course_level = Column(SQLAlchemyEnum('Iniciante', 'Intermediário', 'Avançado', name='course_levels'))

    def __repr__(self):
        return f"<Infoproduct(id={self.id}, name='{self.product_name}', host='{self.infoproduct_host}', niche='{self.market_niche}')>"

class Academia(Product):
    __mapper_args__ = {'polymorphic_identity': 'Academia'}
    location_features = Column(String, comment='Characteristics of the gym\'s location.')
    membership_types = Column(JSON, comment='Types of gym memberships available.')

    def __repr__(self):
        return f"<Academia(id={self.id}, name='{self.product_name}', services_offered={self.services_offered}, target_audience='{self.target_audience}', location_features='{self.location_features}')>"

class Clinica(Product):
    __mapper_args__ = {'polymorphic_identity': 'Clinica'}
    medical_specialties = Column(JSON, comment='List of medical specialties offered by the clinic.')
    insurance_accepted = Column(JSON, comment='Health insurance policies accepted by the clinic.')
    certification_levels = Column(String, comment='Certification levels attained by the clinic.')

    def __repr__(self):
        return f"<Clinica(id={self.id}, name='{self.product_name}', specialties='{self.medical_specialties}')>"

class Varejo(Product):
    __mapper_args__ = {'polymorphic_identity': 'Varejo'}
    product_ranges = Column(JSON, comment='Range of products offered by the retail store.')
    target_market = Column(String, comment='Target market for the retail store.')
    store_location = Column(String, comment='Physical location of the retail store.')
    store_size = Column(DECIMAL, comment='Size of the store in square meters.')

    def __repr__(self):
        return f"<Varejo(id={self.id}, name='{self.product_name}', market='{self.target_market}')>"

class ECommerce(Product):
    __mapper_args__ = {'polymorphic_identity': 'E-commerce'}
    platform_used = Column(String, comment='E-commerce platform used by the business.')
    payment_methods = Column(JSON, comment='Payment methods available on the site.')
    shipping_options = Column(JSON, comment='Shipping options provided by the business.')
    return_policy = Column(String, comment='Return policy of the e-commerce business.')

    def __repr__(self):
        return f"<ECommerce(id={self.id}, name='{self.product_name}', platform='{self.platform_used}')>"

class ObjectiveTrafegoPago(Base):
    __tablename__ = 'objectives_trafego_pago'
    
    id = Column(Integer, primary_key=True)
    briefing_id = Column(Integer, ForeignKey('briefing_trafego_pago.id'))
    goal_title = Column(String)
    current_amount = Column(DECIMAL)
    goal_amount = Column(DECIMAL)
    
    # Relacionamento com StrategicActionsTrafegoPago
    strategic_actions = relationship("StrategicActionsTrafegoPago", back_populates="objective", foreign_keys="[StrategicActionsTrafegoPago.objective_id]")

    # Relacionamento com BriefingTrafegoPago
    briefing = relationship("BriefingTrafegoPago", back_populates="objectives")

    def __repr__(self):
        return f"<ObjectiveTrafegoPago(id={self.id}, goal_title={self.goal_title})>"

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
    updater = relationship("Users", back_populates="updated_briefings_trafego_pago", foreign_keys=[last_updated_by])

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
    objective_id = Column(Integer, ForeignKey('objectives_trafego_pago.id'))
    optimization_id = Column(Integer, ForeignKey('objective_optimizations.id'))
    plan_id = Column(Integer, ForeignKey('plans_trafego_pago.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    action_name = Column(String(255))
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    monthly_budget = Column(Float)
    platform = Column(Text)
    min_cost_per_result_expected = Column(Float)
    max_cost_per_result_expected = Column(Float)
    call_to_action = Column(Text)
    objective_meta_ads_id = Column(Integer, ForeignKey('meta_ads_objectives.id'))

    # Relacionamentos
    budgets = relationship('ActionBudgets', back_populates='action')
    objective = relationship("ObjectiveTrafegoPago", back_populates="strategic_actions", foreign_keys=[objective_id])
    optimization = relationship("ObjectiveOptimization", back_populates="strategic_actions")
    plan = relationship("PlanTrafegoPago", back_populates="strategic_actions")
    client = relationship("Client", back_populates="strategic_actions")
    objective_meta_ads = relationship("MetaAdsObjective", back_populates="strategic_actions")

    def __repr__(self):
        return f"<StrategicActionsTrafegoPago(id={self.id}, action_name={self.action_name})>"

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
    send_date = Column(Date)

    # Adicionando relacionamentos
    client = relationship("Client", back_populates="action_plans_assessoria")
    author = relationship("Users", back_populates="authored_action_plans_assessoria")

class DeliveryControl(Base):

    __tablename__ = 'delivery_control'

    id = Column(Integer, primary_key=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    updated_by = relationship("Users", foreign_keys=[updated_by_id])
    client_id = Column(Integer, ForeignKey('clients.id'))
    client = relationship("Client", back_populates="delivery_controls")
    job_link = Column(String)
    project = Column(String)
    job_category = Column(SQLAlchemyEnum(JobCategoryEnum))
    delivery_control_category = Column(SQLAlchemyEnum(DeliveryCategoryEnum))
    job_title = Column(String)
    job_department = Column(String)
    used_mandalecas = Column(Float, default=0)
    job_creation_date = Column(Date)
    job_start_date = Column(Date)
    job_deadline_date = Column(Date)
    job_finish_date = Column(Date)
    job_status = Column(String)
    user_in_charge_id = Column(Integer, ForeignKey('users.id'))
    user_in_charge = relationship("Users", foreign_keys=[user_in_charge_id], back_populates="delivery_controls_in_charge")
    requested_by_id = Column(Integer, ForeignKey('users.id'))
    requested_by = relationship("Users", foreign_keys=[requested_by_id], back_populates="delivery_controls_requested")
    delivery_category = Column(SQLAlchemyEnum(DeliveryCategoryEnum), nullable=False)

class AttentionPoints(Base):
    __tablename__ = 'pontos_de_atencao'

    id = Column(Integer, primary_key=True, autoincrement=True)
    attention_point = Column(String)
    date = Column(Date)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    client = relationship('Client', back_populates='attention_points')



class WebsiteMaintenance(Base):
    __tablename__ = 'manutencao_site'

    id = Column(Integer, primary_key=True, autoincrement=True)
    notes = Column(String)
    date = Column(Date)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)

    client = relationship('Client', back_populates='manutencao_site')

class BlogText(Base):
    __tablename__ = 'texto_blog'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    author = Column(String)
    creation_date = Column(Date)
    update_date = Column(Date)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)

    client = relationship('Client', back_populates='texto_blog')

class Meetings(Base):
    __tablename__ = 'reunioes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_date = Column(Date, nullable=False)  # Dia que foi entregue
    deadline = Column(Date, nullable=False)  # Deadline até o dia 5
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    client = relationship('Client', back_populates='meetings')


class PlanningDeliveredCopy(Base):
    __tablename__ = 'planejamento_entregue_copy'

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_date = Column(Date, nullable=False)  # Dia que foi entregue
    deadline = Column(Date, nullable=False)  # Deadline pode ser até o dia 15 ou até o dia 25
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    client = relationship('Client', back_populates='plannings_delivered_copy')


class MarketingPlanningReview(Base):
    __tablename__ = 'avaliacao_planejamento_mkt'

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_date = Column(Date, nullable=False)  # Dia que foi entregue
    deadline = Column(Date, nullable=False)  # Deadline entre o dia 15 a 20
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    client = relationship('Client', back_populates='marketing_planning_reviews')
