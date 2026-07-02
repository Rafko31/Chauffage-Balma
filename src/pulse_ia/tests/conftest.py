import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.pulse_ia.models.base import Base
from src.pulse_ia.core.db import get_db
from src.pulse_ia.main import app
import os

@pytest.fixture(scope="session")
def db_engine():
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(database_url)

    # Integration tests against Postgres should use Alembic (handled by Makefile)
    # Unit tests against SQLite can use create_all
    if "postgresql" not in database_url:
        Base.metadata.create_all(bind=engine)

    yield engine

    if "postgresql" not in database_url:
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    del app.dependency_overrides[get_db]
