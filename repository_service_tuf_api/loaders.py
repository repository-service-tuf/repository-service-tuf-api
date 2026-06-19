# SPDX-FileCopyrightText: 2023-2025 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT
import logging
from typing import Any, Dict

from sqlalchemy import Column, String, create_engine
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class RSTUFSettings(Base):
    __tablename__ = "rstuf_settings"
    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)


def load(obj, env=None, silent=True, key=None, filename=None):
    """
    Reads and loads in to "obj" a single key or all keys from database.
    """
    db_server = obj.get("DB_SERVER")
    if not db_server:
        logging.debug("DB_SERVER not found in settings, skipping DB loader")
        return

    try:
        engine = create_engine(db_server)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            if key:
                setting = session.query(RSTUFSettings).filter_by(key=key).first()
                if setting:
                    obj.update({key: setting.value})
            else:
                settings = session.query(RSTUFSettings).all()
                data = {s.key: s.value for s in settings}
                obj.update(data)
    except Exception as e:
        if not silent:
            raise e
        logging.error(f"Error loading settings from DB: {e}")

def write(obj, data: Dict[str, Any]):
    """
    Writes data to database.
    """
    db_server = obj.get("DB_SERVER")
    if not db_server:
        raise AttributeError("DB_SERVER not found in settings")

    engine = create_engine(db_server)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        for key, value in data.items():
            setting = session.query(RSTUFSettings).filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = RSTUFSettings(key=key, value=value)
                session.add(setting)
        session.commit()
