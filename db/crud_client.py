from auth.jwt.verify_token import verify_access_token
from crm.models import Client
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import login_required, commercial_exclusive
from db.config import Session
from auth.login import login
from sqlalchemy import select

view = MainView()
controller = MainController()

@commercial_exclusive
def create_client(access_token: str):
    with Session() as session:
        user_id = verify_access_token(access_token)["sub"]
        client_data = controller.get_client_data()
        client = Client(
            full_name=client_data["full_name"],
            email=client_data["email"],
            phone=client_data["phone"],
            company_id=client_data["company_id"],
            commercial_id=user_id,
            first_contact_date=client_data["first_contact_date"],
            last_contact_date=client_data["last_contact_date"]
        )
        session.add(client)
        session.commit()
        view.success_message(
            f"Your client ({client.full_name}) has been created successfully."
        )

@login_required
def list_clients(access_token: str, filtered: bool = False) -> None:
    with Session() as session:
        user_role_id = int(verify_access_token(access_token)["role_id"])
        user_id = verify_access_token(access_token)["sub"]
        if filtered:
            clients = session.scalars(select(Client).filter(Client.commercial_id == user_id)).all()
        else:
            clients = session.scalars(select(Client)).all()
        view.display_list_clients(clients)

@commercial_exclusive
def update_client(access_token: str, client_id: int=None, full_name: str=None, email: str=None, phone: str=None):
    with Session() as session:
        user_id = verify_access_token(access_token)["sub"]
        if client_id:
            client = session.scalars(select(Client).filter(Client.id == client_id)).one_or_none()   
        if full_name:
            client = session.scalars(select(Client).filter(Client.full_name == full_name)).one_or_none().email = email
        if phone:
            client = session.scalars(select(Client).filter(Client.phone == phone)).one_or_none()
        new_full_name, new_email, new_phone, new_company_id, new_first_contact_date, new_last_contact_date = view.get_client_data()
        session.commit()
        view.success_message(f"Your client ({client.full_name}) has been updated successfully.")
        
@login_required
def view_client(access_token: str, client_id: int):
    with Session() as session:
        client = session.scalars(select(Client).filter(Client.id == client_id)).one_or_none()
        if not client:
            view.wrong_message("OPERATION DENIED: Client not found.")
            return
        view.display_client_detail(client)