
from src.auth.permissions import login_required, require_permission
from src.auth.policy import can_create_event_for_contract, enforce_any_or_assigned
from src.crm.models import Event
from src.data_access.config import Session
from src.data_access.repository import contract_repository, event_repository


class EventLogic:
    @login_required
    def create_event(self, access_token: str, event_data: dict) -> Event:
        with Session() as session:
            # Business rule: check if contract exists and is signed
            contract = contract_repository.get_by_id(event_data["contract_id"], session)
            if not contract:
                raise ValueError("Contract not found.")
            if not contract.is_signed:
                raise ValueError("Cannot create event for an unsigned contract.")
            # Permission: allow global event:create or event:create:own_client if commercial owner
            contract_owner = getattr(contract, "commercial_id", None)
            if contract_owner is not None:
                if not can_create_event_for_contract(access_token, contract_owner):
                    raise PermissionError(
                        "You don't have permission to create an event for this contract."
                    )

            event = event_repository.create(event_data, session)
            session.commit()
            session.refresh(event)
            return event

    @login_required
    def get_events(self,
                   access_token: str,
                   user_id: int,
                   filtered: bool,
                   unassigned_only: bool = False) -> list[Event]:
        with Session() as session:
            # Management can list unassigned events
            if unassigned_only:
                from src.auth.permissions import get_user_id_and_role_from_token
                _, role_id = get_user_id_and_role_from_token(access_token)
                if role_id != 1:  # 1 = management
                    raise PermissionError("Only management can list unassigned events.")
                return event_repository.find_by(session, support_contact_id=None)

            if filtered:
                return event_repository.find_by(session, support_contact_id=user_id)
            return event_repository.get_all(session)

    @require_permission("event:view")
    def get_event_by_id(self, access_token: str, event_id: int) -> Event | None:
        with Session() as session:
            return event_repository.get_by_id(event_id, session)

    @login_required
    def update_event(self,
                    access_token: str,
                    user_id: int,
                    event_id: int,
                    event_data: dict) -> Event | None:
        with Session() as session:
            event = event_repository.get_by_id(event_id, session)
            if not event:
                return
            # Management may update any; support may update only assigned events
            assigned_id = getattr(event, "support_contact_id", None)
            if assigned_id is not None:
                enforce_any_or_assigned(
                    access_token, "event", "update", assigned_id
                )
            updated_event = event_repository.update(event_id, event_data, session)
            session.commit()
            if updated_event:
                session.refresh(updated_event)
            return updated_event

    @require_permission("event:update")
    def assign_support_to_event(self,
                                access_token: str,
                                event_id: int,
                                support_contact_id: int) -> Event | None:
        with Session() as session:
            event = event_repository.get_by_id(event_id, session)
            if not event:
                return

            # Assuming only management can assign support, permission check should be here or in controller

            updated_event = event_repository.update(event_id, {"support_contact_id": support_contact_id}, session)
            session.commit()
            if updated_event:
                session.refresh(updated_event)
            return updated_event


    @require_permission("event:delete")
    def delete_event(self, access_token: str, event_id: int) -> bool:
        with Session() as session:
            event = event_repository.get_by_id(event_id, session)
            if not event:
                return

            deleted = event_repository.delete(event_id, session)
            if deleted:
                session.commit()
            return deleted

event_logic = EventLogic()
