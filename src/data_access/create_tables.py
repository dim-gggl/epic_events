import sentry_sdk
from sqlalchemy import MetaData, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError

from src.auth.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
    ORDERED_DEFAULT_ROLES,
)
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
            try:
                if conn.execute(select(1).select_from(table).limit(1)).first():
                    return True
            except SQLAlchemyError as e:
                sentry_sdk.capture_exception(e)
                continue
    return False


def _ensure_schema_exists() -> None:
    schema_name = getattr(metadata, "schema", None)
    if not schema_name:
        return
    dialect = engine.dialect.name.lower()
    if dialect not in {"postgresql", "postgres"}:
        return
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        raise



def init_db() -> None:
    """
    Ensure the database schema exists and seed roles.

    Always creates any missing tables (idempotent), even if data already exists.
    """
    # Ensure all tables defined on metadata exist, without altering existing ones.
    _ensure_schema_exists()
    metadata.create_all(engine)

    with Session() as session:
        try:
            _seed_roles(session)
            session.commit()
        except Exception as e:
            sentry_sdk.capture_exception(e)
            session.rollback()
            raise

