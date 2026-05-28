from django.contrib import admin
from organizations.models import Organization, User

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'organization', 'role', 'is_active')
    list_filter = ('organization', 'role', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
