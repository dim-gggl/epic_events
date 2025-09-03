from db.config import engine, Session, metadata
from crm.models import Role, User, Client, Company, Contract, Event
from crm.permissions import DEFAULT_ROLE_PERMISSIONS, ORDERED_DEFAULT_ROLES


def _seed_roles(session: Session) -> None:
    for role_name in ORDERED_DEFAULT_ROLES:
        perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        role = session.query(Role).filter(Role.name == role_name).one_or_none()
        if role is None:
            role = Role(name=role_name, permissions=perms)
            session.add(role)
        else:
            role.permissions = perms
    session.flush()

def init_db():
    session = Session()
    metadata.create_all(engine)
    _seed_roles(session)
    session.commit()
    session.close()
