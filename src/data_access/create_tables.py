from sqlalchemy import inspect, select, MetaData
from sqlalchemy.exc import SQLAlchemyError

from src.data_access.config import engine, Session, metadata
from src.crm.models import Role, User, Client, Company, Contract, Event
from src.auth.permissions import DEFAULT_ROLE_PERMISSIONS, ORDERED_DEFAULT_ROLES



def _seed_roles(session: Session) -> None:
    for role_name in ORDERED_DEFAULT_ROLES:
        perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        role = session.query(Role).filter(Role.name == role_name).first()
        if role is None:
            role = Role(name=role_name, permissions=perms)
            session.add(role)
        else:
            role.permissions = perms
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


def init_db(*, force: bool = False) -> None:
    """
    Initialize schema and seed roles safely.
    - Abort if any data already exists (unless force=True).
    - Idempotent on schema creation (create_all).
    """
    if _database_has_any_data() and not force:
        raise RuntimeError(
            "Database already contains data; aborting init. Use force=True to override."
        )

    session = Session()
    try:
        # idempotent: only creates missing tables
        metadata.create_all(engine)  
        _seed_roles(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()