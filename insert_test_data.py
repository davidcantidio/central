from common.models import Client, DeliveryControl
from sqlalchemy.orm import sessionmaker
from common.database import engine
from datetime import date

Session = sessionmaker(bind=engine)
session = Session()

# Adicionar cliente de exemplo
client = Client(name="Ogunjá Revestimentos", monthly_plan_deadline_day=15)
session.add(client)
session.commit()

# Adicionar DeliveryControl de exemplo
delivery_control = DeliveryControl(
    client_id=client.id,
    next_month_plan_sent=True,
    next_month_plan_sent_date=date(2024, 7, 10)
)
session.add(delivery_control)
session.commit()
