from sqlalchemy import select

from src.auth.hashing import hash_password
from src.auth.jwt.token_storage import get_user_info_from_token
from src.auth.permissions import (
    ROLE_ID_TO_NAME,
    UserRoles,
    get_user_role_name_from_token,
)
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
            del data["password"]
        return super().create(data)

    def update(self, id: int, data: dict) -> User | None:
        password = data.get("password")
        if password:
            data["password_hash"] = hash_password(password)
            del data["password"]
        return super().update(id, data)

    def list(self,
            management: bool = False,
            commercial: bool = False,
            support: bool = False,
            ) -> list[User]:


        users = super().get_list()
        result = []

        name_to_id = {name: role_id for role_id, name in ROLE_ID_TO_NAME.items()}

        if management:
            management_role_id = name_to_id.get(UserRoles.MANAGEMENT)
            if management_role_id:
                result.extend([user for user in users if user.role_id == management_role_id])
        if commercial:
            commercial_role_id = name_to_id.get(UserRoles.COMMERCIAL)
            if commercial_role_id:
                result.extend([user for user in users if user.role_id == commercial_role_id])
        if support:
            support_role_id = name_to_id.get(UserRoles.SUPPORT)
            if support_role_id:
                result.extend([user for user in users if user.role_id == support_role_id])

        if any([management, commercial, support]):
            return result
        return users

class ClientManager(EntityManager):
    def __init__(self):
        super().__init__(Client)

    def create(self, data: dict, user_id: int) -> Client:
        # Permission validation done by @require_permission("client:create") decorator
        # Seuls les commerciaux ont cette permission dans DEFAULT_ROLE_PERMISSIONS
        data['commercial_id'] = user_id
        return super().create(data)

    def list(self, user_id: int, filtered: bool = False) -> list[Client]:
        user_role = get_user_role_name_from_token()

        with Session() as session:
            stmt = select(self.entity)

            if filtered:
                stmt = stmt.where(self.entity.commercial_id == user_id)

            # Support ne peut voir que les clients liés à ses événements assignés
            elif user_role == UserRoles.SUPPORT:
                from src.crm.models import Contract, Event
                stmt = (stmt.join(Contract)
                        .join(Event)
                        .where(Event.support_contact_id == user_id))

            return session.scalars(stmt).all()

    def view(self, id: int, session=None) -> Client | None:
        if session is None:
            with Session() as session:
                return self._view_with_support_check(id, session)
        else:
            return self._view_with_support_check(id, session)

    def _view_with_support_check(self, id: int, session) -> Client | None:
        client = super().get_instance(id, session)
        if not client:
            return None

        user_role = get_user_role_name_from_token()
        # Support ne peut voir que les clients liés à ses événements assignés
        if user_role == UserRoles.SUPPORT:
            from src.auth.jwt.token_storage import get_user_info_from_token
            from src.crm.models import Contract, Event
            current_user_info = get_user_info_from_token()

            assigned_client_exists = session.query(
                session.query(Client).join(Contract).join(Event)
                .filter(Client.id == id)
                .filter(Event.support_contact_id == current_user_info['user_id'])
                .exists()
            ).scalar()

            if not assigned_client_exists:
                raise PermissionError(
					"You can only view clients related to your assigned events."
				)

        return client

    def update(self,
              id: int,
              data: dict,
              current_user: dict) -> Client | None:
        with Session() as session:
            client = self.get_instance(id, session)
            if not client:
                return None

            # Base permission validation by
			# @require_permission("client:update:own")
            # Only business logic validation: commercials
			# can only update own clients
            user_role = get_user_role_name_from_token()
            if (user_role == UserRoles.COMMERCIAL
                    and client.commercial_id != current_user['user_id']):
                raise PermissionError(
					"Commercial users can only update their own clients."
				)

            for key, value in data.items():
                if value is not None:
                    setattr(client, key, value)
            session.add(client)
            session.commit()
            session.refresh(client)
            return client


class ContractManager(EntityManager):
    def __init__(self):
        super().__init__(Contract)

    BOOL_FIELDS = {"is_signed", "is_fully_paid"}

    @property
    def is_fully_paid(self) -> bool:
        return self.entity.remaining_amount == 0

    @staticmethod
    def _coerce_boolean(value, field_name: str):
        """Ensure CLI inputs are converted to actual booleans."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "y"}:
                return True
            if normalized in {"false", "0", "no", "n"}:
                return False
            if normalized == "":
                return None
        if isinstance(value, (int, float)):
            if value in {0, 1}:
                return bool(value)
        raise ValueError(f"{field_name.replace('_', ' ')} must be a boolean value.")

    def create(self, data: dict) -> Contract:
        user_info = get_user_info_from_token()
        user_role = get_user_role_name_from_token()

        for bool_field in self.BOOL_FIELDS:
            if bool_field in data:
                data[bool_field] = self._coerce_boolean(data[bool_field], bool_field)

        with Session() as session:
            client = session.get(Client, data["client_id"])
            if not client:
                raise ValueError("Client not found.")

            if not client.commercial_id:
                raise ValueError(
                    "Client must have an assigned commercial before creating a contract."
                )

            if user_role == UserRoles.MANAGEMENT:
                data['commercial_id'] = client.commercial_id
                print(
                    f"Manager creating contract: auto-assigned commercial_id "
                    f"{client.commercial_id} from client relationship"
                )

            elif user_role == UserRoles.COMMERCIAL:
                if client.commercial_id != user_info['user_id']:
                    raise PermissionError("You can only create contracts for your own clients.")
                data['commercial_id'] = user_info['user_id']

        return super().create(data)

    def list(
        self,
        user_id: int,
        filtered: bool = False,
        unsigned: bool = False,
        unpaid: bool = False,
    ) -> list[Contract]:
        user_role = get_user_role_name_from_token()

        with Session() as session:
            stmt = select(self.entity)

            if filtered:
                stmt = stmt.join(Client).where(Client.commercial_id == user_id)

            # Support ne peut voir que les contrats liés à ses événements assignés
            elif user_role == UserRoles.SUPPORT:
                from src.crm.models import Event
                stmt = (stmt.join(Event)
                        .where(Event.support_contact_id == user_id))

            if unsigned:
                stmt = stmt.where(not self.entity.is_signed)
            if unpaid:
                stmt = stmt.where(self.entity.remaining_amount > 0)
            return session.scalars(stmt).all()

    def get_instance(self, id: int, session=None) -> Contract | None:
        if session is None:
            with Session() as session:
                return self._view_with_support_check(id, session)
        else:
            return self._view_with_support_check(id, session)

    def _view_with_support_check(self, id: int, session) -> Contract | None:
        contract = super().get_instance(id, session)
        if not contract:
            return None

        user_role = get_user_role_name_from_token()
        # Support ne peut voir que les contrats liés à ses événements assignés
        if user_role == UserRoles.SUPPORT:
            current_user_info = get_user_info_from_token()

            assigned_contract_exists = session.query(
                session.query(Contract).join(Event)
                .filter(Contract.id == id)
                .filter(Event.support_contact_id == current_user_info['user_id'])
                .exists()
            ).scalar()

            if not assigned_contract_exists:
                raise PermissionError(
                    "You can only view contracts related to your assigned events."
                )

        return contract

    def update(self, id: int, data: dict, user_id: int) -> Contract | None:
        with Session() as session:
            contract = self.get_instance(id, session)
            if not contract:
                return None

            user_role = get_user_role_name_from_token()
            if user_role == UserRoles.COMMERCIAL and contract.client.commercial_id != user_id:
                 raise PermissionError("You can only update contracts for your own clients.")

            for bool_field in self.BOOL_FIELDS:
                if bool_field in data:
                    data[bool_field] = self._coerce_boolean(data[bool_field], bool_field)

            # Filtrer les valeurs None pour éviter d'écraser les champs existants
            for key, value in data.items():
                if value is not None:
                    setattr(contract, key, value)
            session.add(contract)
            session.commit()
            session.refresh(contract)
            return contract

class EventManager(EntityManager):
    def __init__(self):
        super().__init__(Event)

    def create(self, data: dict, current_user: dict) -> Event:
        user_role = get_user_role_name_from_token()

        with Session() as session:
            contract = session.get(Contract, data['contract_id'])
            if not contract:
                raise ValueError("Contract not found.")

            # Tous les rôles: le contrat doit être signé
            if not contract.is_signed:
                raise PermissionError("Cannot create an event for an unsigned contract.")

            # Si c'est un manager, validation supplémentaire déjà couverte par contrat signé
            if user_role == UserRoles.MANAGEMENT:
                pass  # Peut créer pour n'importe quel contrat signé

            # Si c'est un commercial, seulement pour ses propres clients
            elif user_role == UserRoles.COMMERCIAL:
                if contract.client.commercial_id != current_user['user_id']:
                    raise PermissionError(
                        "You can only create events for your own clients' contracts."
                    )

        return super().create(data)

    def list(self,
        	user_id: int,
        	filtered: bool = False,
        	unassigned_only: bool = False) -> list[Event]:
        user_role = get_user_role_name_from_token()

        with Session() as session:
            stmt = select(self.entity)

            if filtered:
                if user_role == UserRoles.SUPPORT:
                    stmt = stmt.where(self.entity.support_contact_id == user_id)
                # Autres filtres spécifiques peuvent être ajoutés ici

            # Support ne peut voir que les événements qui lui sont assignés (par défaut)
            elif user_role == UserRoles.SUPPORT:
                stmt = stmt.where(self.entity.support_contact_id == user_id)

            if unassigned_only:
                stmt = stmt.where(self.entity.support_contact_id.is_(None))

            return session.scalars(stmt).all()

    def update(self, id: int, data: dict, current_user: dict) -> Event | None:
        with Session() as session:
            event = self.get_instance(id, session)
            if not event:
                return None

            # Base permission validation by @require_permission decorator
            # Validation métier spécifique : support ne peut modifier que ses événements assignés
            user_role = get_user_role_name_from_token()
            if (user_role == UserRoles.SUPPORT
                    and event.support_contact_id != current_user['user_id']):
                raise PermissionError("Support users can only update events they are assigned to.")

            for key, value in data.items():
                if value is not None:
                    setattr(event, key, value)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def assign_support(self, event_id: int, support_id: int) -> Event | None:
        with Session() as session:
            event = self.get_instance(event_id, session)
            if not event:
                return None

            from src.auth.permissions import ROLE_ID_TO_NAME

            support_user = session.get(User, support_id)
            if not support_user:
                raise ValueError("Support user not found.")

            # Vérifier que l'utilisateur a bien le rôle support
            user_role_name = ROLE_ID_TO_NAME.get(support_user.role_id, 'unknown')
            if user_role_name != UserRoles.SUPPORT:
                raise ValueError("User must have support role to be assigned to events.")

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

    def list(self, user_id: int = None, **kwargs) -> list[Company]:
        user_role = get_user_role_name_from_token()

        # Support ne peut voir que les entreprises liées à ses événements assignés
        if user_role == UserRoles.SUPPORT and user_id:
            with Session() as session:
                from src.crm.models import Client, Contract, Event
                stmt = (select(self.entity)
                        .join(Client)
                        .join(Contract)
                        .join(Event)
                        .where(Event.support_contact_id == user_id))
                return session.scalars(stmt).all()

        # Pour les autres rôles, utiliser la méthode de base
        return super().list(**kwargs)

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
