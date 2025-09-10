from src.data_access.repository import contract_repository, event_repository
from src.data_access.config import Session
from src.crm.models import Contract, Event
from src.auth.permissions import has_permission_for_contract
from typing import List, Optional

class ContractLogic:
    def create_contract(self, contract_data: dict) -> Contract:
        with Session() as session:
            contract = contract_repository.create(contract_data, session)
            session.commit()
            session.refresh(contract)
            # Load the client relationship to avoid lazy loading issues
            _ = contract.client
            return contract

    def get_contracts(self, access_token: str, user_id: int, filtered: bool) -> List[Contract]:
        with Session() as session:
            # This logic needs to be more sophisticated based on permissions
            # For now, keeping it simple
            if filtered:
                return contract_repository.find_by(session, commercial_id=user_id)
            else:
                return contract_repository.get_all(session)

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        with Session() as session:
            contract = contract_repository.get_by_id(contract_id, session)
            if contract:
                # Load the events relationship to avoid lazy loading issues
                _ = contract.events
            return contract

    def update_contract(self, access_token: str, user_id: int, contract_id: int, contract_data: dict) -> Optional[Contract]:
        with Session() as session:
            contract = contract_repository.get_by_id(contract_id, session)
            if not contract:
                return None
            
            if not has_permission_for_contract(access_token, "update", contract, user_id):
                raise PermissionError("You don't have permission to update this contract.")

            updated_contract = contract_repository.update(contract_id, contract_data, session)
            session.commit()
            if updated_contract:
                session.refresh(updated_contract)
            return updated_contract

    def delete_contract(self, access_token: str, contract_id: int) -> bool:
        with Session() as session:
            contract = contract_repository.get_by_id(contract_id, session)
            if not contract:
                return False

            # Business rule: cannot delete contract with associated events
            events = event_repository.find_by(session, contract_id=contract_id)
            if events:
                raise ValueError("Cannot delete a contract with associated events.")

            deleted = contract_repository.delete(contract_id, session)
            if deleted:
                session.commit()
            return deleted

contract_logic = ContractLogic()
