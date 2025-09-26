import click

from src.cli.help import attach_help, epic_help, render_help_with_logo
from src.crm.controllers.main_controller import main_controller


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def contract(ctx: click.Context):
    """Manage contracts."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(contract)


@epic_help
@contract.command("create")
@click.option("--client-id", help="Client ID", required=False)
@click.option("--commercial-id", help="Commercial ID", required=False)
@click.option("--total-amount", help="Total amount", required=False)
@click.option("--remaining-amount", help="Remaining amount", required=False)
@click.option("--is-signed", type=click.BOOL, help="Is signed", required=False)
@click.option("--is-fully-paid", type=click.BOOL, help="Is fully paid", required=False)
def contract_create(client_id,
                    commercial_id,
                    total_amount,
                    remaining_amount,
                    is_signed,
                    is_fully_paid):
    main_controller.create_contract(
        client_id=client_id,
        commercial_id=commercial_id,
        total_amount=total_amount,
        remaining_amount=remaining_amount,
        is_signed=is_signed,
        is_fully_paid=is_fully_paid,
    )


@epic_help
@contract.command("list")
@click.option("--only-mine",
              is_flag=True,
              help="Show only contracts managed by the logged-in commercial",
              default=False)
@click.option("--unsigned",
              is_flag=True,
              help="Filter to contracts not signed yet",
              default=False)
@click.option("--unpaid",
             is_flag=True,
             help="Filter to contracts not fully paid",
             default=False)
def contract_list(only_mine, unsigned, unpaid):
    """List contracts with optional filters (combinable)."""
    main_controller.list_contracts(only_mine, unsigned, unpaid)


@epic_help
@contract.command("view")
@click.argument("contract_id", type=int)
def contract_view(contract_id):
    main_controller.view_contract(contract_id)


@epic_help
@contract.command("update")
@click.argument("contract_id", type=int)
@click.option("--client-id", help="Client ID", required=False)
@click.option("--commercial-id", help="Commercial ID", required=False)
@click.option("--total-amount", help="Total amount", required=False)
@click.option("--remaining-amount", help="Remaining amount", required=False)
@click.option("--is-signed", type=click.BOOL, help="Is signed", required=False)
@click.option("--is-fully-paid", type=click.BOOL, help="Is fully paid", required=False)
def contract_update(contract_id, client_id, commercial_id, total_amount, remaining_amount, is_signed, is_fully_paid):
    main_controller.update_contract(
        contract_id,
        client_id=client_id,
        commercial_id=commercial_id,
        total_amount=total_amount,
        remaining_amount=remaining_amount,
        is_signed=is_signed,
        is_fully_paid=is_fully_paid,
    )


@epic_help
@contract.command("delete")
@click.argument("contract_id", type=int)
def contract_delete(contract_id):
    main_controller.delete_contract(contract_id)
