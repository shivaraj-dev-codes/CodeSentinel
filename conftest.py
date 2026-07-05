"""Pytest configuration for the Django test suite."""
import django
import pytest


@pytest.fixture(scope="session")
def django_db_setup():
    """Use the test database configured in settings."""
    pass
