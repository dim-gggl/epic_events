from sqlalchemy import MetaData, inspect, select
from sqlalchemy.exc import SQLAlchemyError
import sentry_sdk

from src.auth.permissions import DEFAULT_ROLE_PERMISSIONS, ORDERED_DEFAULT_ROLES
from src.crm.models import PermissionModel, Role
from src.data_access.config import Session, engine, metadata


def _ensure_permission(session: Session, name: str) -> PermissionModel:
    perm = session.query(PermissionModel).filter(PermissionModel.name == name).first()
    if not perm:
        perm = PermissionModel(name=name)
        session.add(perm)
        session.flush()
    return perm


def _seed_roles(session: Session) -> None:
    """Seed roles and synchronize both normalized and array-based permissions."""
    for role_name in ORDERED_DEFAULT_ROLES:
        perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        role = session.query(Role).filter(Role.name == role_name).first()
        if role is None:
            role = Role(name=role_name)
            session.add(role)
            session.flush()

        # Sync array-based permissions for compatibility
        role.permissions = list(perms)

        # Sync normalized permissions
        perm_models = [_ensure_permission(session, p) for p in perms]
        role.permissions_rel = perm_models
    session.flush()

def _database_has_any_data() -> bool:
    """
    Return True if at least one user table exists and contains >= 1 row.
    Engine-agnostic, short-circuits on first hit.
    """
    insp = inspect(engine)
    table_names = insp.get_table_names()
    if not table_names:
        return False

    md = MetaData()
    md.reflect(bind=engine, only=table_names)

    with engine.connect() as conn:
        for name, table in md.tables.items():
            # Optional: skip migration bookkeeping tables
            if name in {"alembic_version"}:
                continue
            try:
                if conn.execute(select(1).select_from(table).limit(1)).first():
                    return True
            except SQLAlchemyError:
                # Non-fatal probe issues (permissions, views, etc.) → ignore and continue
                continue
    return False


def init_db() -> None:
    """
    Ensure the database schema exists and seed roles.

    Always creates any missing tables (idempotent), even if data already exists.
    """
    # Abort early if database already contains data to avoid accidental re-init

    # Ensure all tables defined on metadata exist, without altering existing ones.
    metadata.create_all(engine)

    with Session() as session:
        try:
            _seed_roles(session)
            session.flush()
            session.commit()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            session.rollback()
            raise
        finally:
            session.flush()
            session.commit()

