from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="your@email.com",
        password="Admin123@"
    )
    print("Superuser created")
else:
    print("Superuser already exists")