import click

from src.cli.help import attach_help, epic_help, render_help_with_logo
from src.crm.controllers.main_controller import main_controller


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def company(ctx: click.Context):
    """Manage companies."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(company)


@epic_help
@company.command("create")
@click.option("-n", "--name", help="Company name", required=False)
def company_create(name):
    """Create a company."""
    main_controller.create_company(name=name)


@epic_help
@company.command("list")
def company_list():
    main_controller.list_companies()


@epic_help
@company.command("view")
@click.argument("company_id", type=int)
def company_view(company_id):
    main_controller.view_company(company_id)


@epic_help
@company.command("update")
@click.argument("company_id", type=int)
@click.option("-n", "--name", help="Company name", required=False)
def company_update(company_id, name):
    main_controller.update_company(company_id, name=name)


@epic_help
@company.command("delete")
@click.argument("company_id", type=int)
def company_delete(company_id):
    main_controller.delete_company(company_id)
