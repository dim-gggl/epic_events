from auth.jwt.verify_token import verify_access_token
from crm.models import Client, Contract
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import login_required, require_permission, has_permission
from db.config import Session
from auth.login import login
from sqlalchemy import select
from constants import *
from utils import (
    get_user_id_from_token, check_object_exists, 
    create_error_message, create_success_message,
    create_permission_error_message, create_not_found_error_message
)

view = MainView()
controller = MainController()

@require_permission("client:create")
def create_client(access_token: str):
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
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
            create_success_operation_message("created", "client", 
                                           client.full_name)
        )

@login_required
def list_clients(access_token: str, filtered: bool = False) -> None:
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
        if filtered:
            clients = session.scalars(
                select(Client).filter(Client.commercial_id == user_id)
            ).all()
        else:
            clients = session.scalars(select(Client)).all()
        view.display_list_clients(clients)

@login_required
def update_client(access_token: str, 
                  client_id: int=None, 
                  full_name: str=None, 
                  email: str=None, 
                  phone: str=None) -> None:
    """
    Update a client. Only commercial users 
    can update their own clients.
    """
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
        
        # Get client first
        if client_id:
            client = check_object_exists(session, Client, client_id)
        else:
            view.wrong_message("Client ID is required for update.")
            return
            
        if not client:
            view.wrong_message(create_not_found_error_message("Client"))
            return
            
        # Check permissions - commercial can only update their own clients
        if has_permission(access_token, "client:update:any"):
            # Management can update any client
            pass
        elif has_permission(access_token, "client:update:own"):
            # Commercial can only update their own clients
            if client.commercial_id != user_id:
                view.wrong_message(
                    f"{OPERATION_DENIED}: {ONLY_OWN_RECORDS}"
                )
                return
        else:
            view.wrong_message(
                create_permission_error_message("update", "clients")
            )
            return
            
        # Get new client data from user input
        client_data = controller.get_client_data()
        
        # Update client fields
        client.full_name = client_data["full_name"]
        client.email = client_data["email"]
        client.phone = client_data["phone"]
        client.company_id = client_data["company_id"]
        client.first_contact_date = client_data["first_contact_date"]
        client.last_contact_date = client_data["last_contact_date"]
        
        session.commit()
        view.success_message(
            create_success_operation_message("updated", "client", 
                                           client.full_name)
        )
        
@login_required
def view_client(access_token: str, client_id: int):
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
        client = check_object_exists(session, Client, client_id)
        
        if not client:
            view.wrong_message(create_not_found_error_message("Client"))
            return
            
        # Check permissions
        if has_permission(access_token, "client:view:any"):
            # Management can view any client
            pass
        elif has_permission(access_token, "client:view:own"):
            # Commercial can only view their own clients
            if client.commercial_id != user_id:
                view.wrong_message(
                    f"{OPERATION_DENIED}: {ONLY_OWN_RECORDS}"
                )
                return
        elif has_permission(access_token, "client:view:assigned"):
            # Support can view clients for events they are assigned to
            # For now, we'll allow viewing - this would need more complex logic
            # to check if they have events assigned for this client
            pass
        else:
            view.wrong_message(
                create_permission_error_message("view", "clients")
            )
            return
            
        view.display_client_detail(access_token, client)

@require_permission("client:delete")
def delete_client(access_token: str, client_id: int):
    """Delete a client. Only management can delete clients."""
    with Session() as session:
        client = check_object_exists(session, Client, client_id)
        
        if not client:
            view.wrong_message(create_not_found_error_message("Client"))
            return
            
        # Check if client has associated contracts
        associated_contracts = session.scalars(
            select(Contract).filter(Contract.client_id == client_id)
        ).all()
        if associated_contracts:
            view.wrong_message(
                f"{OPERATION_DENIED}: {CANNOT_DELETE_WITH_ASSOCIATIONS}"
            )
            return
            
        session.delete(client)
        session.commit()
        view.success_message(
            create_success_operation_message("deleted", "client", 
                                           client.full_name)
        )