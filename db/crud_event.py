from auth.jwt.verify_token import verify_access_token
from crm.models import Event
from crm.controllers import MainController
from crm.views.views import MainView
from crm.permissions import require_permission, has_permission, login_required
from db.config import Session
from sqlalchemy import select

view = MainView()
controller = MainController()

@login_required
def create_event(access_token: str):
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        
        # Check permissions - both commercial and management can create events
        if not (has_permission(access_token, "event:create:own_client") or 
                has_permission(access_token, "event:create:any")):
            view.wrong_message("OPERATION DENIED: You don't have permission to create events.")
            return
            
        event_data = controller.get_event_data()
        event = Event(
            contract_id=event_data["contract_id"],
            title=event_data["title"],
            full_address=event_data["full_address"],
            start_date=event_data["start_date"],
            end_date=event_data["end_date"],
            participant_count=event_data["participant_count"],
            notes=event_data["notes"],
            support_contact_id=event_data.get("support_contact_id", "Not assigned")
        )
        session.add(event)
        session.commit()
        view.success_message(f"Event ({event.title}) has been created successfully.")

@login_required
def update_event(access_token: str, event_id: int):
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        event = session.scalars(select(Event).filter(Event.id == event_id)).one_or_none()
        
        if not event:
            view.wrong_message("OPERATION DENIED: Event not found.")
            return
            
        # Check permissions
        if has_permission(access_token, "event:update:any"):
            # Management can update any event
            pass
        elif has_permission(access_token, "event:update:assigned"):
            # Support can update events assigned to them
            if event.support_contact_id != user_id:
                view.wrong_message("OPERATION DENIED: You can only update events assigned to you.")
                return
        else:
            view.wrong_message("OPERATION DENIED: You don't have permission to update events.")
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
        view.success_message(f"Event ({event.title}) has been updated successfully.")

@login_required    
def list_events(access_token: str, filtered: bool = False):
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        
        # Check permissions and determine what events to show
        if has_permission(access_token, "event:list:any"):
            # Management can see all events
            if filtered:
                # Filter to show only events they manage
                events = session.scalars(select(Event)).all()  # For now, show all
            else:
                events = session.scalars(select(Event)).all()
        elif has_permission(access_token, "event:list:own_client"):
            # Commercial can see events for their clients
            # This would need a more complex query to join with contracts and clients
            events = session.scalars(select(Event)).all()  # For now, simplified
        elif has_permission(access_token, "event:list:assigned"):
            # Support can see events assigned to them
            events = session.scalars(
                select(Event).filter(Event.support_contact_id == user_id)
            ).all()
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to list events."
            )
            return
            
        view.display_events(events)

@login_required
def view_event(access_token: str, event_id: int):
    with Session() as session:
        user_id = int(verify_access_token(access_token)["sub"])
        event = session.scalars(
            select(Event).filter(Event.id == event_id)
        ).one_or_none()
        
        if not event:
            view.wrong_message("OPERATION DENIED: Event not found.")
            return
            
        # Check permissions
        if has_permission(access_token, "event:view:any"):
            # Management can view any event
            pass
        elif has_permission(access_token, "event:view:own_client"):
            # Commercial can view events for their clients
            # This would need more complex logic to check if it's their client
            pass
        elif has_permission(access_token, "event:view:assigned"):
            # Support can view events assigned to them
            if event.support_contact_id != user_id:
                view.wrong_message(
                    "OPERATION DENIED: You can only view events assigned to you."
                )
                return
        else:
            view.wrong_message(
                "OPERATION DENIED: You don't have permission to view events."
            )
            return
            
        view.display_event(event)

@require_permission("event:update:any")
def assign_support_to_event(
    access_token: str, event_id: int, support_contact_id: int = None) -> None:
    """
    Simple function to assign a support contact to an event.
    Only management can use this function.
    """
    with Session() as session:
        event = session.scalars(
            select(Event).filter(Event.id == event_id)
        ).one_or_none()
        
        if not event:
            view.wrong_message("OPERATION DENIED: Event not found.")
            return
            
        if support_contact_id is None:
            # Prompt for support contact ID
            support_contact_id = int(view.get_support_contact_id())
        
        # Update the event with the new support contact
        event.support_contact_id = support_contact_id
        session.commit()
        
        view.success_message(
            f"Event '{event.title}' has been assigned to "
            f"support contact ID {support_contact_id}.")

@require_permission("event:delete")
def delete_event(access_token: str, event_id: int):
    """Delete an event. Only management can delete events."""
    with Session() as session:
        event = session.scalars(
            select(Event).filter(Event.id == event_id)
        ).one_or_none()
        
        if not event:
            view.wrong_message("OPERATION DENIED: Event not found.")
            return
            
        session.delete(event)
        session.commit()
        view.success_message(
            f"Event '{event.title}' (ID: {event_id}) has been deleted successfully."
        )