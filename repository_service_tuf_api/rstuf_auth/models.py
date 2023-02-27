# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(
        DateTime, nullable=True, default=lambda: datetime.utcnow()
    )

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<Username: {self.username}"


class Scope(Base):
    __tablename__ = "scope"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=False)

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<Scope: {self.name}>"


class UserScope(Base):
    __tablename__ = "user_scope"

    user_id = Column(
        Integer, ForeignKey("user.id"), nullable=False, primary_key=True
    )
    scope_id = Column(
        Integer, ForeignKey("scope.id"), nullable=False, primary_key=True
    )

    User = relationship("User", foreign_keys=[user_id])
    Scope = relationship("Scope", foreign_keys=[scope_id])
