import click

from src.cli.help import attach_help, epic_help, render_help_with_logo
from src.crm.controllers.main_controller import main_controller


@epic_help
@click.group(invoke_without_command=True)
@click.pass_context
def user(ctx: click.Context):
    """Manage users."""
    if ctx.invoked_subcommand is None:
        render_help_with_logo(ctx)

attach_help(user)


@epic_help
@user.command("create")
@click.option("-u", "--username", help="Username", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-r", "--role-id", type=int, help="Role ID (1=mgmt, 2=comm, 3=support)", required=False)
def user_create(username, full_name, email, role_id):
    """Create a new user with proper validation through the service layer."""
    main_controller.register_user(
        username=username,
        full_name=full_name,
        email=email,
        password=None,  # Password will always be prompted securely
        role_id=role_id,
    )


@epic_help
@user.command("list")
@click.option("-M","--management", help="Management users", is_flag=True, required=False)
@click.option("-C","--commercial", help="Commercial users", is_flag=True, required=False)
@click.option("-S","--support", help="Support users", is_flag=True, required=False)
def user_list(management=False, commercial=False, support=False):
    main_controller.list_users(management, commercial, support)

@epic_help
@user.command("view")
@click.argument("user_id", type=int)
def user_view(user_id):
    main_controller.view_user(user_id)


@epic_help
@user.command("update")
@click.argument("user_id", type=int)
@click.option("-u", "--username", help="Username", required=False)
@click.option("-n", "--full-name", help="Full name", required=False)
@click.option("-e", "--email", help="Email", required=False)
@click.option("-r", "--role-id", type=int, help="Role ID (1 -> management, 2 -> commercial, 3 -> support)", required=False)
def user_update(user_id, username, full_name, email, role_id):
    main_controller.update_user(
        user_id,
        username=username,
        full_name=full_name,
        email=email,
        role_id=role_id,
    )


@epic_help
@user.command("delete")
@click.argument("user_id", type=int)
def user_delete(user_id):
    main_controller.delete_user(user_id)


@epic_help
@user.command("update-password")
@click.argument("user_id", type=int)
def user_update_password(user_id):
    """Reset a user's password (management only)."""
    main_controller.reset_user_password(user_id)
