import click

from src.cli.help import attach_help, epic_help, render_help_with_logo
from src.crm.controllers.main_controller import main_controller


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def event(ctx: click.Context):
    """Manage events."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(event)


@epic_help
@event.command("create")
@click.option("-c","--contract-id", type=int, help="Contract ID", required=False)
@click.option("-t", "--title", type=str, help="Event title", required=False)
@click.option("-fa", "--full-address", type=str, help="Full address", required=False)
@click.option("-s", "--support-contact-id", type=int, help="Support user ID", required=False)
@click.option("-sd", "--start-date", type=str, help="Start date (dd/mm/yyyy or dd/mm/yyyy HH:MM)",
              required=False)
@click.option("-e", "--end-date", type=str, help="End date (dd/mm/yyyy or dd/mm/yyyy HH:MM)",
              required=False)
@click.option("-pc", "--participant-count", type=int, help="Participant count", required=False)
@click.option("-n", "--notes", type=str, help="Notes", required=False)
def event_create(contract_id,
                 title,
                 full_address,
                 support_contact_id,
                 start_date,
                 end_date,
                 participant_count,
                 notes):
    main_controller.create_event(contract_id=contract_id,
                                title=title,
                                full_address=full_address,
                                support_contact_id=support_contact_id,
                                start_date=start_date,
                                end_date=end_date,
                                participant_count=participant_count,
                                notes=notes,)



@epic_help
@event.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your events", default=False)
@click.option("--unassigned", is_flag=True,
              help="Show only unassigned events (management only)",
              default=False)
def event_list(only_mine, unassigned):
    """List events with optional restriction (`--only-mine`) or unassigned filter."""
    main_controller.list_events(only_mine, unassigned)


@epic_help
@event.command("view")
@click.argument("event_id", type=int)
def event_view(event_id):
    main_controller.view_event(event_id)


@epic_help
@event.command("update")
@click.argument("event_id", type=int)
@click.option("-c", "--contract-id", type=int, help="Contract ID", required=False)
@click.option("-t", "--title", type=str, help="Event title", required=False)
@click.option("-a", "--full-address", type=str, help="Full address", required=False)
@click.option("-s", "--support-contact-id", type=int, help="Support user ID", required=False)
@click.option("-sd", "--start-date", type=str, help="Start date (dd/mm/yyyy or dd/mm/yyyy HH:MM)",
              required=False)
@click.option("-e", "--end-date", type=str,
              help="End date (dd/mm/yyyy or dd/mm/yyyy HH:MM)",
              required=False)
@click.option("--participant-count", type=int, help="Participant count", required=False)
@click.option("--notes", type=str, help="Notes", required=False)
def event_update(event_id,
                 contract_id,
                 title,
                 full_address,
                 support_contact_id,
                 start_date,
                 end_date,
                 participant_count,
                 notes):
    main_controller.update_event(
        event_id,
        contract_id=contract_id,
        title=title,
        full_address=full_address,
        support_contact_id=support_contact_id,
        start_date=start_date,
        end_date=end_date,
        participant_count=participant_count,
        notes=notes
    )


@epic_help
@event.command("assign-support")
@click.argument("event_id", type=int)
@click.argument("support_id", type=int)
def assign_support(event_id, support_id):
    main_controller.assign_support_to_event(event_id, support_id)


@epic_help
@event.command("delete")
@click.argument("event_id", type=int)
def event_delete(event_id):
    main_controller.delete_event(event_id)
