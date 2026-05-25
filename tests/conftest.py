import os
import sys
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from config import Config
from models import db as _db

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    BASE_DIR = os.path.join(os.path.dirname(__file__), '..')

@pytest.fixture(scope='session')
def app():
    """Create application for testing with in-memory SQLite."""
    from app import create_app
    app = create_app(TestConfig)
    
    with app.app_context():
        # Create all tables for test
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def db(app):
    """Provide database session for tests."""
    with app.app_context():
        yield _db
        _db.session.rollback()

@pytest.fixture(scope='function')
def session(app, db):
    """Database session for direct ORM operations."""
    return db.session