from organizations.models import User

try:
    user = User.objects.get(email="analyst@example.com")
    user.set_password("testpass123")
    user.save()
    print("Password fixed successfully")
except Exception as e:
    print(e)