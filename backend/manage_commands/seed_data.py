#!/usr/bin/env python
"""
Seed database with test data.
Run: python manage.py shell < manage_commands/seed_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breathe.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create a simple test user for login
user, created = User.objects.get_or_create(
    username='analyst',
    defaults={
        'email': 'analyst@example.com',
        'first_name': 'Anna',
        'last_name': 'Analyst',
        'is_active': True,
    }
)

if created:
    user.set_password('testpass123')
    user.save()
    print(f"✅ Created user: {user.email}")
else:
    print(f"✅ User already exists: {user.email}")

print("\n✅ Seed data loaded successfully!")
print(f"Login with:\n  Email: analyst@example.com\n  Password: testpass123")

