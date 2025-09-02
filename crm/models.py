from enum import StrEnum
from typing import Union
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean,
    CheckConstraint, Text, UniqueConstraint, Index, Table, text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import Numeric, ARRAY
from sqlalchemy.ext.mutable import MutableList

from db.config import Base
from exceptions import OperationDeniedError


class Permission(StrEnum):
    LIST_USERS = "list_users"
    VIEW_USER = "view_user"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    LIST_ROLES = "list_roles"
    VIEW_ROLE = "view_role"
    CREATE_ROLE = "create_role"
    UPDATE_ROLE = "update_role"
    DELETE_ROLE = "delete_role"
    ASSIGN_ROLE = "assign_role"
    LIST_CLIENTS = "list_clients"
    VIEW_CLIENT = "view_client"
    CREATE_CLIENT = "create_client"
    UPDATE_CLIENT = "update_client"
    DELETE_CLIENT = "delete_client"
    LIST_CONTRACTS = "list_contracts"
    VIEW_CONTRACT = "view_contract"
    CREATE_CONTRACT = "create_contract"
    UPDATE_CONTRACT = "update_contract"
    DELETE_CONTRACT = "delete_contract"
    LIST_EVENTS = "list_events"
    VIEW_EVENT = "view_event"
    CREATE_EVENT = "create_event"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"


PermLike = Union[str, Permission]


class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), unique=True, nullable=False)
    users = relationship("User", back_populates="role", passive_deletes=True)
    permissions: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)),
        default=list,
        server_default=text("'{}'::text[]"),
        nullable=False,
    )

    def __repr__(self):
        return f"<Role (id={self.id}), \"{self.name}\">"

    def __str__(self):
        return self.name
    
    def get_users_count(self):
        return len(self.users)
    
    def has_users(self):
        return bool(self.users)
    
    def get_active_users(self):
        return [user for user in self.users if user.is_active]
    
    def can_(self, permission: PermLike) -> bool:
        perm_value = permission.value if isinstance(permission, Permission) else permission
        return perm_value in self.permissions


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    role_id = Column(
        Integer,
        ForeignKey("role.id", ondelete="RESTRICT"),
        nullable=False
    )
    role = relationship("Role", back_populates="users")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    is_active = Column(Boolean, nullable=False, server_default="true")
    last_login = Column(DateTime(timezone=True), nullable=True)

    managed_clients = relationship("Client", back_populates="commercial", passive_deletes=True)
    managed_contracts = relationship("Contract", back_populates="commercial", passive_deletes=True)
    supported_events = relationship("Event", back_populates="support_contact", passive_deletes=True)

    refresh_token_hash = Column(String(255), nullable=True)

    def __repr__(self):
        role_name = self.role.name if getattr(self, "role", None) else "Unknown"
        return f"<User {role_name} (id={self.id}): {self.username}>"
    
    def __str__(self):
        return self.full_name


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    clients = relationship("Client", back_populates="company", passive_deletes=True)


class Client(Base):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    phone = Column(String(32), nullable=True)

    company_id = Column(Integer, ForeignKey("company.id", ondelete="SET NULL"), nullable=True)
    company = relationship("Company", back_populates="clients")

    commercial_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    commercial = relationship("User", back_populates="managed_clients")

    first_contact_date = Column(DateTime(timezone=True), nullable=False)
    last_contact_date  = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Client (id={self.id}): {self.full_name} " \
               f"commercial_id={self.commercial_id} " \
               f"company_id={self.company_id}>"
    
    def __str__(self):
        company_name = self.company.name if getattr(self, "company", None) else "No company"
        return f"{self.full_name} ({company_name})"


class Contract(Base):
    __tablename__ = "contract"
    id = Column(Integer, primary_key=True, autoincrement=True)

    client_id = Column(Integer, ForeignKey("client.id", ondelete="RESTRICT"), nullable=False)
    client = relationship("Client", backref="contracts")

    commercial_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    commercial = relationship("User", back_populates="managed_contracts")

    total_amount = Column(Numeric(12, 2), nullable=False)
    remaining_amount = Column(Numeric(12, 2), nullable=False)

    is_signed = Column(Boolean, nullable=False, server_default="false")
    is_fully_paid = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    events = relationship("Event", back_populates="contract", uselist=True, passive_deletes=True)
    

    __table_args__ = (
        CheckConstraint("remaining_amount >= 0"),
    )

    def __repr__(self):
        return f"<Contract (id={self.id}): " \
               f"client_id={self.client_id} " \
               f"commercial_id={self.commercial_id}>"
    
    def __str__(self):
        return f"{self.client.full_name} - {self.total_amount}€"


class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)

    contract_id = Column(Integer, ForeignKey("contract.id", ondelete="CASCADE"), nullable=False)
    contract = relationship("Contract", back_populates="events")

    full_address = Column(String(256), nullable=False)

    support_contact_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    support_contact = relationship("User", back_populates="supported_events")

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True),   nullable=False)
    participant_count = Column(Integer, nullable=False, server_default="0")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_event_end_after_start"),
        CheckConstraint("participant_count >= 0", name="ck_event_participants_nonneg"),
        Index("ix_event_start_date", "start_date"),
        Index("ix_event_support", "support_contact_id"),
    )
    
    def __repr__(self):
        return f"<Event (id={self.id} " \
               f"contract_id={self.contract_id} " \
               f"support_contact_id={self.support_contact_id})>"
    
    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"
