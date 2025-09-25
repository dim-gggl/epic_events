from sqlalchemy import select

from src.auth.hashing import hash_password
from src.crm.controllers.base_manager import EntityManager
from src.crm.models import Client, Company, Contract, Event, Role, User
from src.data_access.config import Session


class UserManager(EntityManager):
    def __init__(self):
        super().__init__(User)

    def create(self, data: dict) -> User:
        password = data.get("password")
        if password:
            data["password_hash"] = hash_password(password)
            del data["password"]  # Remove password from data dict
        return super().create(data)

    def update(self, id: int, data: dict) -> User | None:
        password = data.get("password")
        if password:
            data["password_hash"] = hash_password(password)
            del data["password"]  # Remove password from data dict
        return super().update(id, data)

    def list(self,
            management: bool = False,
            commercial: bool = False,
            support: bool = False,
            ) -> list[User]:
        users = super().list()
        result = []
        if management:
            result.extend([
                user for user in users if user.role_id == 1
            ])
        if commercial:
            result.extend([
                user for user in users if user.role_id == 2
            ])
        if support:
            result.extend([
                user for user in users if user.role_id == 3
            ])
        if any([management, commercial, support]):
            return result
        return users

class ClientManager(EntityManager):
    def __init__(self):
        super().__init__(Client)

    def create(self, data: dict, user_id: int) -> Client:
        from src.auth.jwt.token_storage import get_user_info_from_token
        user_info = get_user_info_from_token()

        # Seuls les commerciaux peuvent créer des clients
        if user_info and user_info['role_id'] == 1:  # Management
            raise PermissionError(
                "Managers cannot create clients. Only commercial users can create clients."
            )

        data['commercial_id'] = user_id
        return super().create(data)

    def list(self, user_id: int, filtered: bool = False) -> list[Client]:
        with Session() as session:
            stmt = select(self.entity)
            if filtered:
                stmt = stmt.where(self.entity.commercial_id == user_id)
            return session.scalars(stmt).all()

    def update(self,
              id: int,
              data: dict,
              current_user: dict) -> Client | None:
        with Session() as session:
            client = self.view(id, session)
            if not client:
                return None

            # Managers ne peuvent pas modifier les clients
            if current_user['role_id'] == 1:  # Management
                raise PermissionError(
                    "Managers cannot update clients. Only commercial users can update their clients."
                )

            # Commerciaux ne peuvent modifier que leurs propres clients
            if current_user['role_id'] == 2 and client.commercial_id != current_user['user_id']:
                raise PermissionError("Commercial users can only update their own clients.")

            for key, value in data.items():
                setattr(client, key, value)
            session.add(client)
            session.commit()
            session.refresh(client)
            return client

class ContractManager(EntityManager):
    def __init__(self):
        super().__init__(Contract)

    def create(self, data: dict) -> Contract:
        from src.auth.jwt.token_storage import get_user_info_from_token
        user_info = get_user_info_from_token()

        with Session() as session:
            client = session.get(Client, data["client_id"])
            if not client:
                raise ValueError("Client not found.")

            # Si c'est un manager, vérifier que client-commercial sont déjà liés
            if user_info and user_info['role_id'] == 1:  # Management
                if not data.get("commercial_id"):
                    raise ValueError("Commercial ID is required for contract creation.")
                if client.commercial_id != data.get("commercial_id"):
                    raise PermissionError(
                        "Managers can only create contracts between already linked "
                        "client-commercial pairs."
                    )

            # Si c'est un commercial, il ne peut créer que pour ses propres clients
            elif user_info and user_info['role_id'] == 2:  # Commercial
                if client.commercial_id != user_info['user_id']:
                    raise PermissionError("You can only create contracts for your own clients.")
                # Assurer que le commercial_id correspond à l'utilisateur actuel
                data['commercial_id'] = user_info['user_id']

        return super().create(data)

    def list(
        self,
        user_id: int,
        filtered: bool = False,
        unsigned: bool = False,
        unpaid: bool = False,
    ) -> list[Contract]:
        with Session() as session:
            stmt = select(self.entity)
            if filtered:
                stmt = stmt.join(Client).where(Client.commercial_id == user_id)
            if unsigned:
                stmt = stmt.where(not self.entity.is_signed)
            if unpaid:
                stmt = stmt.where(self.entity.remaining_amount > 0)
            return session.scalars(stmt).all()

    def update(self, id: int, data: dict, user_id: int) -> Contract | None:
        with Session() as session:
            contract = self.view(id, session)
            if not contract:
                return None

            from src.auth.jwt.token_storage import get_user_info_from_token
            user_info = get_user_info_from_token()
            if user_info and user_info['role_id'] == 2 and contract.client.commercial_id != user_id:
                 raise PermissionError("You can only update contracts for your own clients.")

            for key, value in data.items():
                setattr(contract, key, value)
            session.add(contract)
            session.commit()
            session.refresh(contract)
            return contract

class EventManager(EntityManager):
    def __init__(self):
        super().__init__(Event)

    def create(self, data: dict, current_user: dict) -> Event:
        with Session() as session:
            contract = session.get(Contract, data['contract_id'])
            if not contract:
                raise ValueError("Contract not found.")

            # Tous les rôles: le contrat doit être signé
            if not contract.is_signed:
                raise PermissionError("Cannot create an event for an unsigned contract.")

            # Si c'est un manager, validation supplémentaire déjà couverte par contrat signé
            if current_user['role_id'] == 1:  # Management
                pass  # Peut créer pour n'importe quel contrat signé

            # Si c'est un commercial, seulement pour ses propres clients
            elif current_user['role_id'] == 2:  # Commercial
                if contract.client.commercial_id != current_user['user_id']:
                    raise PermissionError(
                        "You can only create events for your own clients' contracts."
                    )

        return super().create(data)

    def list(
        self,
        user_id: int,
        filtered: bool = False,
        unassigned_only: bool = False,
    ) -> list[Event]:
        with Session() as session:
            stmt = select(self.entity)
            from src.auth.jwt.token_storage import get_user_info_from_token
            user_info = get_user_info_from_token()
            if user_info and user_info['role_id'] == 3 and filtered:
                stmt = stmt.where(self.entity.support_contact_id == user_id)

            if unassigned_only:
                stmt = stmt.where(self.entity.support_contact_id.is_(None))

            return session.scalars(stmt).all()

    def update(self, id: int, data: dict, current_user: dict) -> Event | None:
        with Session() as session:
            event = self.view(id, session)
            if not event:
                return None

            if current_user['role_id'] == 3 and event.support_contact_id != current_user['user_id']:
                raise PermissionError("Support users can only update events they are assigned to.")

            for key, value in data.items():
                setattr(event, key, value)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def assign_support(self, event_id: int, support_id: int) -> Event | None:
        with Session() as session:
            event = self.view(event_id, session)
            if not event:
                return None

            support_user = session.get(User, support_id)
            if not support_user or support_user.role_id != 3:
                raise ValueError("Invalid support user ID.")

            event.support_contact_id = support_id
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

class RoleManager(EntityManager):
    def __init__(self):
        super().__init__(Role)

class CompanyManager(EntityManager):
    def __init__(self):
        super().__init__(Company)

user_manager = UserManager()
client_manager = ClientManager()
contract_manager = ContractManager()
event_manager = EventManager()
role_manager = RoleManager()
company_manager = CompanyManager()

manager_repertory = {
    "user": user_manager,
    "client": client_manager,
    "contract": contract_manager,
    "event": event_manager,
    "role": role_manager,
    "company": company_manager
}
