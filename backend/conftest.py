import pytest
from django.contrib.auth import get_user_model
from organizations.models import Organization
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def organization():
    return Organization.objects.create(
        name="Test Org",
        slug="test-org"
    )


@pytest.fixture
def analyst_user(organization):
    user = User.objects.create_user(
        email="analyst@test.com",
        username="analyst",
        password="testpass123",
        organization=organization,
        role="analyst"
    )
    return user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, analyst_user):
    """Return API client with analyst authenticated"""
    api_client.force_authenticate(user=analyst_user)
    return api_client
