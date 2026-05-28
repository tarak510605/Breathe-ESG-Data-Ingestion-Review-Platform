import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class Organization(models.Model):
    """Multi-tenant root entity."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    
    # Organization settings
    default_emission_unit = models.CharField(
        max_length=50,
        default='kg_co2e',
        choices=[('kg_co2e', 'kg CO2e'), ('metric_tons_co2e', 'metric tons CO2e')]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations_organization'
        indexes = [
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model scoped to organization."""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('analyst', 'Analyst'),
        ('reviewer', 'Reviewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')
    is_active = models.BooleanField(default=True)
    
    # Override M2M relationships to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='organization_users',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='organization_users',
        blank=True,
        help_text='Specific permissions for this user.'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations_user'
        unique_together = [['email', 'organization']]
        indexes = [
            models.Index(fields=['organization', 'email']),
            models.Index(fields=['organization', 'role']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.organization.name})"
