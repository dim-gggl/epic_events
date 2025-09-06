from auth.jwt.verify_token import verify_access_token
from crm.models import Client, Contract, Event, Company
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import login_required, commercial_exclusive, management_exclusive
from db.config import Session
from auth.login import login
from sqlalchemy import select


view = MainView()
controller = MainController()

@management_exclusive
def create_contract(access_token: str, 
                    client_id: int=None, 
                    commercial_id: int=None, 
                    total_amount: float=None, 
                    remaining_amount: float=None, 
                    is_signed: bool=None, 
                    is_fully_paid: bool=None):
    contract_data = controller.get_contract_data(commercial_id)
    if not client_id:
        client_id = contract_data["client_id"]
    if not commercial_id:
        commercial_id = contract_data["commercial_id"]
    if not total_amount:
        total_amount = contract_data["total_amount"]
    if not remaining_amount:
        remaining_amount = contract_data["remaining_amount"]
    if not is_signed:
        is_signed = contract_data["is_signed"]
    if not is_fully_paid:
        is_fully_paid = contract_data["is_fully_paid"]
    with Session() as session:
        contract = Contract(
            client_id=client_id,
            commercial_id=commercial_id,
            total_amount=total_amount,
            remaining_amount=remaining_amount,
            is_signed=is_signed,
            is_fully_paid=is_fully_paid
        )
        session.add(contract)
        session.commit()
        view.success_message(f"Your contract ({contract.id}) has been created successfully.")