# Definindo ENUMs
business_types = Enum('local_business', 'virtual_business', 'infoproduct', 'b2b', name='business_types')
departments = Enum('Administrativo', 'Marketing', 'Criação', 'Redes Sociais', 'Tráfego Pago', 'RH', 'Produção', name='departments')
contract_type = Enum('CLT', 'PJ Mensal', 'PJ por produção', name='contract_type')
role = Enum('Gerente', 'Analista', 'Assistente', 'Diretor de Arte', 'Copywriter', 'Redator', 'Produção', name='role')
vacation_status = Enum('Agendada', 'Disponível', 'Em Férias', name='vacation_status')
employee_payment_type = Enum('Por Job', 'Por Mês', name='charge_type')
action_plan_status = Enum('Aguardando Início', 'Em Andamento', 'Em Criação', 'Em Orçamento', 'Em Aprovação', 'Reprovado', 'Aprovado', 'Em execução', 'Concluído', 'Cancelado', 'Stand By', name='action_plan_status')
product_types = Enum('Imob', 'Evento', 'Varejo', 'Ecommerce', name='product_types')
report_analysis_title = Enum('Instagram - Seguidores', 'Instagram - Posts', 'Instagram - Impulsionamentos', 'Instagram - Próximos Passos', 'Instagram - Pontos de Atenção', 'Linkedin - Traduzindo Números' 'Linkedin - Análise das Publicações', 'Linkedin - Análise dos Seguidores',  'Linkedin - Próximos Passos', 'Google Analytics', 'Google Ads', 'Meta Ads', 'Tik Tok Ads', 'Tráfego Pago - Pontos de Atenção', 'Tráfego Pago - Próximos Passos', 'Linkedin Ads' 'Tik Tok - Análise dos Seguidores', 'Tik Tok - Análise dos Posts', 'Tik Tok - Próximos Passos', 'Tik Tok - Pontos de Atenção' )
platforms = Enum('Meta Ads', 'Google Ads', 'TikTok Ads', 'Linkedin Ads')
meta_ads_objectives = Enum(
    'OUTCOME_AWARENESS',
    'OUTCOME_TRAFFIC',
    'LINK_CLICKS',
    'OUTCOME_ENGAGEMENT',
    'QUALITY_CALL',
    'MESSAGES',
    'LEAD_GENERATION',
    'OUTCOME_SALES',
    'WEBSITE',
    'OUTCOME_APP_PROMOTION',
    'OUTCOME_LEADS',
    'PHONE_CALL',
    'PRODUCT_CATALOG_SALES',
    'STORE_VISITS',
    name='meta_ads_objectives'
)

meta_ads_call_to_actions = Enum(
    'BOOK_NOW', 'REQUEST_QUOTE', 'CALL_NOW', 'CHARITY_DONATE', 'CONTACT_US', 
    'DONATE_NOW', 'MESSAGE', 'OPEN_APP', 'PLAY_NOW', 'SHOP_NOW', 'SIGN_UP', 
    'WATCH_NOW', 'GET_OFFER', 'GET_OFFER_VIEW', 'BOOK_APPOINTMENT', 'LISTEN', 
    'EMAIL', 'LEARN_MORE', 'REQUEST_APPOINTMENT', 'GET_DIRECTIONS', 'BUY_TICKETS', 
    'PLAY_MUSIC', 'VISIT_GROUP', 'SHOP_ON_FACEBOOK', 'LOCAL_DEV_PLATFORM', 
    'INTERESTED', 'WOODHENGE_SUPPORT', 'BECOME_A_VOLUNTEER', 'VIEW_SHOP', 
    'PURCHASE_GIFT_CARDS', 'FOLLOW_PAGE', 'ORDER_FOOD', 'VIEW_INVENTORY', 
    'MOBILE_CENTER', 'VIEW_MENU')


departments = ('Redes Sociais', '<i class="fa-solid fa-hashtag"></i>', "Atuamos como marketing terceirizado do cliente, para as empresas que não possuem um marketing na sua estrutura e atuamos também como um braço do marketing das empresas que possuem este departamento internamente. Neste segundo caso a nossa atuação se assemelha um pouco com às agências tradicionais. Porém o nosso envolvimento 360° e a nossa entrega cuidadosa, são a nossa marca registrada!" ),
('Assessoria de Marketing', '<i class="fa-solid fa-comments-dollar"></i>', "Gerenciamos e produzimos conteúdos para as Redes Sociais dos clientes." ),
('Tráfego Pago', '<i class="fa-solid fa-bullhorn"></i>', "Planejamos e executamos campanhas de mídia paga na internet" ),

services = Enum('Assessoria', 'Consultoria', 'Pacote de Criação','Redes Sociais', 'Tráfego Pago', 'Site', 'Identidade Visual/Branding', 'Material Gráfico', 'Editoração e Diagramação', 'Material Digital', 'Sinalização', 'Publicidade/Propaganda', 'Vídeos', 'Geral' 'Honorários Produção', 'Desconto'))