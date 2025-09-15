
from src.auth.permissions import login_required, require_permission
from src.auth.policy import enforce_any_or_own
from src.crm.models import Client
from src.data_access.config import Session
from src.data_access.repository import client_repository, contract_repository


class ClientLogic:
    @require_permission("client:create")
    def create_client(self, access_token: str, client_data: dict, commercial_id: int) -> Client:
        with Session() as session:
            client_data["commercial_id"] = commercial_id
            client = client_repository.create(client_data, session)
            session.commit()
            session.refresh(client)
            return client

    @login_required
    def get_clients(self, access_token: str, user_id: int, filtered: bool) -> list[Client]:
        with Session() as session:
            if filtered:
                return client_repository.find_by(session, commercial_id=user_id)
            else:
                return client_repository.get_all(session)

    @require_permission("client:view")
    def get_client_by_id(self, access_token: str, client_id: int) -> Client | None:
        with Session() as session:
            return client_repository.get_by_id(client_id, session)

    @login_required
    def update_client(self,
                      access_token: str,
                      user_id: int,
                      client_id: int,
                      client_data: dict) -> Client | None:
        with Session() as session:
            client = client_repository.get_by_id(client_id, session)
            if not client:
                return
            # Enforce any-or-own semantics according to role permissions
            enforce_any_or_own(access_token, "client", "update", client.commercial_id)
            updated_client = client_repository.update(client_id, client_data, session)
            session.commit()
            if updated_client:
                session.refresh(updated_client)
            return updated_client

    @require_permission("client:delete")
    def delete_client(self, access_token: str, client_id: int) -> bool:
        with Session() as session:
            client = client_repository.get_by_id(client_id, session)
            if not client:
                return

            # Business rule: cannot delete client with associated contracts
            contracts = contract_repository.find_by(session, client_id=client_id)
            if contracts:
                raise ValueError("Cannot delete a client with associated contracts.")

            deleted = client_repository.delete(client_id, session)
            if deleted:
                session.commit()
            return deleted

client_logic = ClientLogic()
