"""
Pytest configuration and shared fixtures.
"""
import pytest
from django.conf import settings


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Configure test database settings.
    """
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database.
    """
    pass


@pytest.fixture
def api_client():
    """
    Create a Django test client for API testing.
    """
    from django.test import Client
    return Client()
