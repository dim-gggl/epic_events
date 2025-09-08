from auth.jwt.verify_token import verify_access_token
from crm.models import Client, Contract
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import login_required, require_permission, has_permission
from db.config import Session
from auth.login import login
from sqlalchemy import select

view = MainView()
controller = MainController()

@require_permission("client:create")
def create_client(access_token: str):
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
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
        user_id = int(verify_access_token(access_token)["sub"])
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
        user_id = int(verify_access_token(access_token)["sub"])
        
        # Get client first
        if client_id:
            client = session.scalars(
                select(Client).filter(Client.id == client_id)
            ).one_or_none()   
        else:
            view.wrong_message("Client ID is required for update.")
            return
            
        if not client:
            view.wrong_message("Client not found.")
            return
            
        # Check permissions - commercial can only update their own clients
        if has_permission(access_token, "client:update:any"):
            # Management can update any client
            pass
        elif has_permission(access_token, "client:update:own"):
            # Commercial can only update their own clients
            if client.commercial_id != user_id:
                view.wrong_message(
                    "OPERATION DENIED: You can only update your own clients."
                )
                return
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to update clients."
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
            f"Client ({client.full_name}) has been updated successfully."
        )
        
@login_required
def view_client(access_token: str, client_id: int):
    with Session() as session:
        user_id = int(
            verify_access_token(access_token)["sub"]
        )
        client = session.scalars(
            select(Client).filter(Client.id == client_id)
        ).one_or_none()
        
        if not client:
            view.wrong_message("OPERATION DENIED: Client not found.")
            return
            
        # Check permissions
        if has_permission(access_token, "client:view:any"):
            # Management can view any client
            pass
        elif has_permission(access_token, "client:view:own"):
            # Commercial can only view their own clients
            if client.commercial_id != user_id:
                view.wrong_message(
                    "OPERATION DENIED: You can only view your own clients."
                )
                return
        elif has_permission(access_token, "client:view:assigned"):
            # Support can view clients for events they are assigned to
            # For now, we'll allow viewing - this would need more complex logic
            # to check if they have events assigned for this client
            pass
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to view clients."
            )
            return
            
        view.display_client_detail(access_token, client)

@require_permission("client:delete")
def delete_client(access_token: str, client_id: int):
    """Delete a client. Only management can delete clients."""
    with Session() as session:
        client = session.scalars(
            select(Client).filter(Client.id == client_id)
        ).one_or_none()
        
        if not client:
            view.wrong_message("OPERATION DENIED: Client not found.")
            return
            
        # Check if client has associated contracts
        associated_contracts = session.scalars(
            select(Contract).filter(Contract.client_id == client_id)
        ).all()
        if associated_contracts:
            view.wrong_message(
                "OPERATION DENIED: Cannot delete client with associated contracts."
            )
            return
            
        session.delete(client)
        session.commit()
        view.success_message(
            f"Client '{client.full_name}' (ID: {client_id}) has been deleted successfully."
        )