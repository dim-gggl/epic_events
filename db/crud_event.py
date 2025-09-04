from auth.jwt.verify_token import verify_access_token
from crm.models import Event
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import commercial_exclusive, management_exclusive, login_required
from db.config import Session
from sqlalchemy import select

view = MainView()
controller = MainController()

@commercial_exclusive
def create_event(access_token: str):
    with Session() as session:
        user_id = verify_access_token(access_token)["sub"]
        event_data = controller.get_event_data()
        event = Event(
            contract_id=event_data["contract_id"],
            title=event_data["title"],
            full_address=event_data["full_address"],
            start_date=event_data["start_date"],
            end_date=event_data["end_date"],
            participant_count=event_data["participant_count"],
            notes=event_data["notes"]
        )
        session.add(event)
        session.commit()
        view.success_message(f"Your event ({event.title}) has been created successfully.")

@management_exclusive
def update_event(access_token: str, event_id: int):
    with Session() as session:
        event = session.scalars(select(Event).filter(Event.id == event_id)).one_or_none()
        if not event:
            view.wrong_message("OPERATION DENIED: Event not found.")
            return
        event_data = controller.get_event_data()
        event.title = event_data.get("title", event.title)
        event.contract_id = event_data.get("contract_id", event.contract_id)
        event.full_address = event_data.get("full_address", event.full_address)
        event.support_contact_id = event_data.get("support_contact_id", event.support_contact_id)
        event.start_date = event_data.get("start_date", event.start_date)
        event.end_date = event_data.get("end_date", event.end_date)
        event.participant_count = event_data.get("participant_count", event.participant_count)
        event.notes = event_data.get("notes", event.notes)
        session.commit()
        view.success_message(f"Your event ({event.title}) has been updated successfully.")

@login_required    
def list_events(access_token: str):
    with Session() as session:
        user_id = verify_access_token(access_token)["sub"]
        events = session.scalars(select(Event).filter(Event.commercial_id == user_id)).all()
        view.display_events(events)

@login_required
def view_event(access_token: str, event_id: int):
    with Session() as session:
        event = session.scalars(select(Event).filter(Event.id == event_id)).one_or_none()
        if not event:
            view.wrong_message("OPERATION DENIED: Event not found.")
            return
        view.display_event(event)