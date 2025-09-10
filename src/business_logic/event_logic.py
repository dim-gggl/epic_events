from src.data_access.repository import event_repository, contract_repository
from src.data_access.config import Session
from src.crm.models import Event, Contract
from src.auth.permissions import has_permission_for_event
from typing import List, Optional

class EventLogic:
    def create_event(self, access_token: str, event_data: dict) -> Event:
        with Session() as session:
            # Business rule: check if contract exists and is signed
            contract = contract_repository.get_by_id(event_data["contract_id"], session)
            if not contract:
                raise ValueError("Contract not found.")
            if not contract.is_signed:
                raise ValueError("Cannot create event for an unsigned contract.")
            
            event = event_repository.create(event_data, session)
            session.commit()
            session.refresh(event)
            return event

    def get_events(self, access_token: str, user_id: int, filtered: bool) -> List[Event]:
        with Session() as session:
            # This logic needs to be more sophisticated based on permissions
            if filtered:
                return event_repository.find_by(session, support_contact_id=user_id)
            else:
                return event_repository.get_all(session)

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        with Session() as session:
            return event_repository.get_by_id(event_id, session)

    def update_event(self, access_token: str, user_id: int, event_id: int, event_data: dict) -> Optional[Event]:
        with Session() as session:
            event = event_repository.get_by_id(event_id, session)
            if not event:
                return None

            if not has_permission_for_event(access_token, "update", event, user_id):
                raise PermissionError("You don't have permission to update this event.")

            updated_event = event_repository.update(event_id, event_data, session)
            session.commit()
            if updated_event:
                session.refresh(updated_event)
            return updated_event
            
    def assign_support_to_event(self, access_token: str, event_id: int, support_contact_id: int) -> Optional[Event]:
        with Session() as session:
            event = event_repository.get_by_id(event_id, session)
            if not event:
                return None

            # Assuming only management can assign support, permission check should be here or in controller
            
            updated_event = event_repository.update(event_id, {"support_contact_id": support_contact_id}, session)
            session.commit()
            if updated_event:
                session.refresh(updated_event)
            return updated_event


    def delete_event(self, access_token: str, event_id: int) -> bool:
        with Session() as session:
            event = event_repository.get_by_id(event_id, session)
            if not event:
                return False

            deleted = event_repository.delete(event_id, session)
            if deleted:
                session.commit()
            return deleted

event_logic = EventLogic()
