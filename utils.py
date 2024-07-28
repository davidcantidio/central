from datetime import date, datetime

def check_plan_status(client, delivery_controls):
    today = date.today()
    deadline_day = client.monthly_plan_deadline_day
    deadline_date = date(today.year, today.month, deadline_day)

    plan_sent = False
    plan_sent_date = None
    plan_status = "Atrasado"

    for control in delivery_controls:
        if control.next_month_plan_sent:
            plan_sent = True
            plan_sent_date = control.next_month_plan_sent_date
            if plan_sent_date and plan_sent_date <= deadline_date:
                plan_status = "Enviado"
            break

    if not plan_sent and today <= deadline_date:
        plan_status = "Dentro do Prazo"

    return plan_status, plan_sent_date
