
from src.auth.permissions import login_required, require_permission
from src.auth.policy import enforce_any_or_own
from src.crm.models import Contract
from src.data_access.config import Session
from src.data_access.repository import contract_repository, event_repository


class ContractLogic:
    @require_permission("contract:create")
    def create_contract(self, access_token: str, contract_data: dict) -> Contract:
        with Session() as session:
            contract = contract_repository.create(contract_data, session)
            session.commit()
            session.refresh(contract)
            _ = contract.client
            return contract

    @login_required
    def get_contracts(self, access_token: str, user_id: int, filtered: bool) -> list[Contract]:
        with Session() as session:
            if filtered:
                return contract_repository.find_by(session, commercial_id=user_id)
            else:
                return contract_repository.get_all(session)

    @require_permission("contract:view")
    def get_contract_by_id(self, access_token: str, contract_id: int) -> Contract | None:
        with Session() as session:
            contract = contract_repository.get_by_id(contract_id, session)
            if contract:
                _ = contract.events
            return contract

    @login_required
    def update_contract(self,
                        access_token: str,
                        user_id: int,
                        contract_id: int,
                        contract_data: dict) -> Contract | None:
        with Session() as session:
            contract = contract_repository.get_by_id(contract_id, session)
            if not contract:
                return
            # Enforce any-or-own (commercial owner) semantics
            enforce_any_or_own(access_token, "contract", "update", contract.commercial_id)
            updated_contract = contract_repository.update(contract_id, contract_data, session)
            session.commit()
            if updated_contract:
                session.refresh(updated_contract)
            return updated_contract

    @require_permission("contract:delete")
    def delete_contract(self, access_token: str, contract_id: int) -> bool:
        with Session() as session:
            contract = contract_repository.get_by_id(contract_id, session)
            if not contract:
                return

            events = event_repository.find_by(session, contract_id=contract_id)
            if events:
                raise ValueError("Cannot delete a contract with associated events.")

            deleted = contract_repository.delete(contract_id, session)
            if deleted:
                session.commit()
            return deleted

contract_logic = ContractLogic()
