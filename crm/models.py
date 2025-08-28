from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean,
    CheckConstraint, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.config import Base
from exceptions import OperationDeniedError


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), unique=True, nullable=False)
    users = relationship("User", back_populates="role", passive_deletes=True)

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


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # TODO: Add password hashing
    password_hash = Column(String(255), nullable=False)

    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="RESTRICT")
    )
    role = relationship("Role", back_populates="users")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    is_active = Column(Boolean, nullable=False, server_default="true")
    last_login = Column(DateTime(timezone=True), nullable=True)

    managed_clients = relationship("Client", back_populates="commercial", passive_deletes=True)
    managed_contracts = relationship("Contract", back_populates="commercial", passive_deletes=True)
    supported_events = relationship("Event", back_populates="support_contact", passive_deletes=True)

    def __repr__(self):
        if self.role.name:
            return f"<User {self.role.name} (id={self.id}): {self.username}>"
        return f"<User (id={self.id}): {self.full_name}>"
    
    def __str__(self):
        return self.full_name


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    clients = relationship("Client", back_populates="company", passive_deletes=True)


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    phone = Column(String(32), nullable=True)

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
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
        return f"{self.full_name} ({self.company.name})"


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, autoincrement=True)

    client_id = Column(Integer, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False)
    client = relationship("Client", backref="contracts")

    commercial_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    commercial = relationship("User", back_populates="managed_contracts")

    total_amount = Column(Numeric(12, 2), nullable=False)
    remaining_amount = Column(Numeric(12, 2), nullable=False)
    is_signed = Column(Boolean, nullable=False, server_default="false")
    is_fully_paid = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    event = relationship("Event", back_populates="contract", uselist=False, passive_deletes=True)

    def __repr__(self):
        return f"<Contract (id={self.id}): " \
               f"client_id={self.client_id} " \
               f"commercial_id={self.commercial_id}>"
    
    def __str__(self):
        return f"{self.client.full_name} - {self.total_amount}€"


class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_address = Column(String(256), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    events = relationship("Event", back_populates="venue", passive_deletes=True)

    def __repr__(self):
        return f"<Venue (id={self.id}): {self.full_address}>"
    
    def __str__(self):
        return self.full_address


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)

    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, unique=True)
    contract = relationship("Contract", back_populates="event")

    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="SET NULL"), nullable=True)
    venue = relationship("Venue", back_populates="events")

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
               f"venue_id={self.venue_id} " \
               f"support_contact_id={self.support_contact_id})>"
    
    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"
