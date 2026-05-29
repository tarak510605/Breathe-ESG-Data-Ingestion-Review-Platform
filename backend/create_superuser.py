from django.contrib.auth import get_user_model

User = get_user_model()

print("Running create_superuser.py")

if not User.objects.filter(username="admin").exists():
    print("Creating admin user...")
    User.objects.create_superuser(
        username="admin",
        email="your@email.com",
        password="Admin123@"
    )
    print("Superuser created")
else:
    print("Superuser already exists")