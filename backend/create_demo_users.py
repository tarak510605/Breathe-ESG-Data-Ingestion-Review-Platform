from django.contrib.auth import get_user_model

User = get_user_model()

users = [
    {
        "email": "analyst@example.com",
        "password": "testpass123",
    },
    {
        "email": "reviewer@example.com",
        "password": "testpass123",
    },
]

for user_data in users:
    user, created = User.objects.get_or_create(
        email=user_data["email"]
    )

    if created:
        user.set_password(user_data["password"])
        user.save()
        print(f"Created {user.email}")
    else:
        print(f"{user.email} already exists")