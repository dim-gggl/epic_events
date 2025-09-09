from auth.jwt.verify_token import verify_access_token
from crm.models import Client, Contract, Event, Company
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import login_required, require_permission, has_permission
from db.config import Session
from auth.login import login
from sqlalchemy import select


view = MainView()
controller = MainController()


@require_permission("contract:create")
def create_contract(access_token: str, 
                    client_id: int=None, 
                    commercial_id: int=None, 
                    total_amount: float=None, 
                    remaining_amount: float=None, 
                    is_signed: bool=None, 
                    is_fully_paid: bool=None):
    """Create a contract linking a commercial with a client."""
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
        view.success_message(
            f"Contract ({contract.id}) has been created successfully."
        )

@login_required
def list_contracts(access_token: str, filtered: bool = False):
    """List contracts based on user permissions."""
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        
        if has_permission(access_token, "contract:list:any"):
            # Management can see all contracts
            contracts = session.scalars(select(Contract)).all()
        elif has_permission(access_token, "contract:list:own"):
            # Commercial can see their own contracts
            contracts = session.scalars(
                select(Contract).filter(Contract.commercial_id == user_id)
            ).all()
        elif has_permission(access_token, "contract:view:assigned"):
            # Support can see contracts for their assigned events
            # This needs a join with events
            from crm.models import Event
            contracts = session.scalars(
                select(Contract).join(Event).filter(Event.support_contact_id == user_id)
            ).all()
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to list contracts."
            )
            return
            
        view.display_contracts(contracts)

@login_required
def view_contract(access_token: str, contract_id: int):
    """View a specific contract based on user permissions."""
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        contract = session.scalars(
            select(Contract).filter(Contract.id == contract_id)
        ).one_or_none()
        
        if not contract:
            view.wrong_message("OPERATION DENIED: Contract not found.")
            return
            
        # Check permissions
        if has_permission(access_token, "contract:view:any"):
            # Management can view any contract
            pass
        elif has_permission(access_token, "contract:view:own"):
            # Commercial can view their own contracts
            if contract.commercial_id != user_id:
                view.wrong_message(
                    "OPERATION DENIED: You can only view your own contracts."
                )
                return
        elif has_permission(access_token, "contract:view:assigned"):
            # Support can view contracts for their assigned events
            from crm.models import Event
            assigned_event = session.scalars(
                select(Event).filter(Event.contract_id == contract_id, Event.support_contact_id == user_id)
            ).first()
            if not assigned_event:
                view.wrong_message(
                    "OPERATION DENIED: You can only view contracts for your assigned events."
                )
                return
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to view contracts."
            )
            return
            
        view.display_contract(contract)

@require_permission("contract:update")
def update_contract(access_token: str, contract_id: int, **kwargs):
    """Update a contract based on user permissions."""
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        contract = session.scalars(
            select(Contract).filter(Contract.id == contract_id)
        ).one_or_none()
        
        if not contract:
            view.wrong_message("OPERATION DENIED: Contract not found.")
            return
            
        # Check permissions
        if has_permission(access_token, "contract:update:any"):
            # Management can update any contract
            pass
        elif has_permission(access_token, "contract:update:own"):
            # Commercial can update their own contracts
            if contract.commercial_id != user_id:
                view.wrong_message(
                    "OPERATION DENIED: You can only update your own contracts."
                )
                return
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to update contracts."
            )
            return
            
        # Get updated data if not provided via kwargs
        if not any(kwargs.values()):
            contract_data = controller.get_contract_data(contract.commercial_id)
            for key, value in contract_data.items():
                if key != 'commercial_id':  # Don't change the commercial
                    setattr(contract, key, value)
        else:
            # Update with provided values
            for key, value in kwargs.items():
                if value is not None and hasattr(contract, key):
                    setattr(contract, key, value)
                    
        session.commit()
        view.success_message(
            f"Contract ({contract.id}) has been updated successfully."
        )

@require_permission("contract:delete")
def delete_contract(access_token: str, contract_id: int):
    """Delete a contract. Only management can delete contracts."""
    with Session() as session:
        contract = session.scalars(
            select(Contract).filter(Contract.id == contract_id)
        ).one_or_none()
        
        if not contract:
            view.wrong_message("OPERATION DENIED: Contract not found.")
            return
            
        # Check if contract has associated events
        from crm.models import Event
        associated_events = session.scalars(
            select(Event).filter(Event.contract_id == contract_id)
        ).all()
        if associated_events:
            view.wrong_message("OPERATION DENIED: Cannot delete contract with associated events.")
            return
            
        session.delete(contract)
        session.commit()
        view.success_message(f"Contract ({contract_id}) has been deleted successfully.")