from django.contrib.auth import get_user_model

print("=== CREATE SUPERUSER SCRIPT STARTED ===")

User = get_user_model()

try:
    if not User.objects.filter(username="admin").exists():
        print("Creating admin...")
        User.objects.create_superuser(
            username="admin",
            email="your@email.com",
            password="Admin123@"
        )
        print("Superuser created")
    else:
        print("Superuser already exists")
except Exception as e:
    print("ERROR:", e)