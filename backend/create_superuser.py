from django.contrib.auth import get_user_model

User = get_user_model()

email = "admin@example.com"
password = "Admin123@"

user, created = User.objects.get_or_create(
    username="admin",
    defaults={
        "email": email,
        "is_superuser": True,
        "is_staff": True,
    }
)

user.email = email
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()

print(f"Admin user ready: {email}")