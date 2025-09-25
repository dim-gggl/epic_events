import click

from src.cli.help import attach_help, epic_help, render_help_with_logo
from src.crm.controllers.main_controller import main_controller


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def client(ctx: click.Context):
    """Manage clients."""
    if not ctx.invoked_subcommand:
        render_help_with_logo(ctx)

attach_help(client)


@epic_help
@client.command("create")
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-p", "--phone", help="Phone", required=False)
@click.option("-c", "--company-id", help="Company ID", required=False)
@click.option("-f", "--first-contact-date", help="First contact date", required=False)
@click.option("-l", "--last-contact-date", help="Last contact date", required=False)
def client_create(full_name, email, phone, company_id, first_contact_date, last_contact_date):
    """Create a new client."""
    main_controller.create_client(
        full_name=full_name,
        email=email,
        phone=phone,
        company_id=company_id,
        first_contact_date=first_contact_date,
        last_contact_date=last_contact_date,
    )


@epic_help
@client.command("list")
@click.option("--only-mine", is_flag=True, help="Show only your clients", default=False)
def client_list(only_mine):
    """List clients."""
    main_controller.list_clients(only_mine)


@epic_help
@client.command("view")
@click.argument("client_id", type=int)
def client_view(client_id):
    """View client details."""
    main_controller.view_client(client_id)


@epic_help
@client.command("update")
@click.argument("client_id", type=int)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-p", "--phone", help="Phone", required=False)
@click.option("-c", "--company-id", help="Company ID", required=False)
@click.option("-f", "--first-contact-date", help="First contact date", required=False)
@click.option("-l", "--last-contact-date", help="Last contact date", required=False)
def client_update(client_id, full_name, email, phone, company_id, first_contact_date, last_contact_date):
    """Update client information."""
    main_controller.update_client(
        client_id,
        full_name=full_name,
        email=email,
        phone=phone,
        company_id=company_id,
        first_contact_date=first_contact_date,
        last_contact_date=last_contact_date,
    )


@epic_help
@client.command("delete")
@click.argument("client_id", type=int)
def client_delete(client_id):
    """Delete a client."""
    main_controller.delete_client(client_id)
