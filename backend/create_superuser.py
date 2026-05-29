from django.contrib.auth import get_user_model
from organizations.models import Organization

User = get_user_model()

org, _ = Organization.objects.get_or_create(
    slug="default",
    defaults={"name": "Default Organization"}
)

user, created = User.objects.get_or_create(
    username="admin",
    defaults={
        "email": "admin@example.com",
        "organization": org,
        "is_staff": True,
        "is_superuser": True,
    }
)

user.organization = org
user.email = "admin@example.com"
user.is_staff = True
user.is_superuser = True
user.set_password("Admin123@")
user.save()

print("Admin user ready")