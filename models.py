from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Float,
    Boolean,
    CheckConstraint,
    Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db_config import Base


class User(Base):
    __tablename__ = "users"
    # Required fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, max_length=255)

    # Role definition
    role = relationship("Role", back_populates="users")
    role_id = Column(Integer, ForeignKey("roles.id"))

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Authentication
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)

    # Relationships user is going to manage depending on his role
    managed_clients = relationship("Client", back_populates="commercial")
    managed_contracts = relationship("Contract", back_populates="commercial")
    supported_events = relationship("Event", back_populates="support_contact")


class Role(Base):
    # Role choices
    CHOICES = [
        ("management", "Management"),
        ("commercial", "Commercial"),
        ("support", "Support"),
        ("admin", "Admin")
    ]

    # Role table
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, choices=CHOICES)
    users = relationship("User", back_populates="role")


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Client(Base):
    __tablename__ = "clients"
    # Basic Information
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, max_length=255)
    phone = Column(String, nullable=True)

    # Company definition
    company = relationship("Company", ondelete="SET NULL")
    company_id = Column(Integer, ForeignKey("companies.id"))

    # Epic Events related fields
    commercial = relationship("User", back_populates="managed_clients")
    commercial_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    first_contact_date = Column(DateTime, nullable=False)
    last_contact_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Contract(Base):
    __tablename__ = "contracts"
    # Identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    client = relationship("Client", ondelete="RESTRICT")
    client_id = Column(Integer, ForeignKey("clients.id"))
    commercial = relationship("User", back_populates="managed_contracts")
    commercial_id = Column(Integer, ForeignKey("users.id"))

    # Filtering fields
    total_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    is_signed = Column(Boolean, default=False)
    is_fully_paid = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Venue(Base):
    __tablename__ = "venues"
    # Identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_address = Column(String, unique=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Event(Base):
    __tablename__ = "events"
    # Identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    contract = relationship("Contract", ondelete="CASCADE")
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    venue = relationship("Venue", ondelete="SET NULL")
    venue_id = Column(Integer, ForeignKey("venues.id"))
    support_contact = relationship("User", back_populates="supported_events")
    support_contact_id = Column(Integer, ForeignKey("users.id"))

    # Filtering fields
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    participant_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("end_date > start_date"),
    )
