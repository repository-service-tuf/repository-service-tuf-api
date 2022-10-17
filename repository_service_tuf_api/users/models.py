# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

user_scope = Table(
    "user_scope",
    Base.metadata,
    Column("user_id", ForeignKey("user.id")),
    Column("scope_id", ForeignKey("scope.id")),
)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    scopes = relationship("Scope", secondary="user_scope", backref="allowed")

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<Username: {self.username}"


class Scope(Base):
    __tablename__ = "scope"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<Scope: {self.name}>"
