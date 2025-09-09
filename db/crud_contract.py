from auth.jwt.verify_token import verify_access_token
from crm.models import Client, Contract, Event, Company
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

@require_permission("contract:create:any")
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
            create_success_operation_message("created", "contract", 
                                           str(contract.id))
        )

@login_required
def list_contracts(access_token: str, filtered: bool = False):
    """List contracts based on user permissions."""
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
        
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
                select(Contract).join(Event).filter(
                    Event.support_contact_id == user_id
                )
            ).all()
        else:
            view.wrong_message(
                create_permission_error_message("list", "contracts")
            )
            return
            
        view.display_contracts(contracts)

@login_required
def view_contract(access_token: str, contract_id: int):
    """View a specific contract based on user permissions."""
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
        contract = check_object_exists(session, Contract, contract_id)
        
        if not contract:
            view.wrong_message(create_not_found_error_message("Contract"))
            return
            
        # Check permissions
        if has_permission(access_token, "contract:view:any"):
            # Management can view any contract
            pass
        elif has_permission(access_token, "contract:view:own"):
            # Commercial can view their own contracts
            if contract.commercial_id != user_id:
                view.wrong_message(
                    f"{OPERATION_DENIED}: {ONLY_OWN_RECORDS}"
                )
                return
        elif has_permission(access_token, "contract:view:assigned"):
            # Support can view contracts for their assigned events
            from crm.models import Event
            assigned_event = session.scalars(
                select(Event).filter(
                    Event.contract_id == contract_id, 
                    Event.support_contact_id == user_id
                )
            ).first()
            if not assigned_event:
                view.wrong_message(
                    f"{OPERATION_DENIED}: {ONLY_ASSIGNED_RECORDS}"
                )
                return
        else:
            view.wrong_message(
                create_permission_error_message("view", "contracts")
            )
            return
            
        view.display_contract(contract)

@login_required
def update_contract(access_token: str, contract_id: int, **kwargs):
    """Update a contract based on user permissions."""
    with Session() as session:
        user_id = get_user_id_from_token(access_token)
        contract = check_object_exists(session, Contract, contract_id)
        
        if not contract:
            view.wrong_message(create_not_found_error_message("Contract"))
            return
            
        # Check permissions
        if has_permission(access_token, "contract:update:any"):
            # Management can update any contract
            pass
        elif has_permission(access_token, "contract:update:own"):
            # Commercial can update their own contracts
            if contract.commercial_id != user_id:
                view.wrong_message(
                    f"{OPERATION_DENIED}: {ONLY_OWN_RECORDS}"
                )
                return
        else:
            view.wrong_message(
                create_permission_error_message("update", "contracts")
            )
            return
            
        # Get updated data if not provided via kwargs
        if not any(kwargs.values()):
            contract_data = controller.get_contract_data(contract.commercial_id)
            for key, value in contract_data.items():
                if key != "commercial_id":  # Don't change the commercial
                    setattr(contract, key, value)
        else:
            # Update with provided values
            for key, value in kwargs.items():
                if value is not None and hasattr(contract, key):
                    setattr(contract, key, value)
                    
        session.commit()
        view.success_message(
            create_success_operation_message("updated", "contract", 
                                           str(contract.id))
        )

@require_permission("contract:delete")
def delete_contract(access_token: str, contract_id: int):
    """Delete a contract. Only management can delete contracts."""
    with Session() as session:
        contract = check_object_exists(session, Contract, contract_id)
        
        if not contract:
            view.wrong_message(create_not_found_error_message("Contract"))
            return
            
        # Check if contract has associated events
        from crm.models import Event
        associated_events = session.scalars(
            select(Event).filter(Event.contract_id == contract_id)
        ).all()
        if associated_events:
            view.wrong_message(
                f"{OPERATION_DENIED}: {CANNOT_DELETE_WITH_ASSOCIATIONS}"
            )
            return
            
        session.delete(contract)
        session.commit()
        view.success_message(
            create_success_operation_message("deleted", "contract", 
                                           str(contract_id))
        )