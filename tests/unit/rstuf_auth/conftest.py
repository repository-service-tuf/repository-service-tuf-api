# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repository_service_tuf_api.rstuf_auth.models import Base


@pytest.fixture
def db_session():

    db_url = (
        f"sqlite:///{os.path.join(os.getenv('DATA_DIR'), 'rstuf_auth.sqlite')}"
    )

    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    yield session

    Base.metadata.drop_all(bind=engine)
