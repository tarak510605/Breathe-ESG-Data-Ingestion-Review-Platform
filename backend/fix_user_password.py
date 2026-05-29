from organizations.models import User, Organization

org, _ = Organization.objects.get_or_create(
    slug="default",
    defaults={"name": "Default Organization"}
)

user, created = User.objects.get_or_create(
    email="analyst@example.com",
    defaults={
        "username": "analyst@example.com",
        "organization": org,
        "role": "analyst",
    }
)

user.organization = org
user.username = "analyst@example.com"
user.set_password("testpass123")
user.save()

print("Analyst user ready")