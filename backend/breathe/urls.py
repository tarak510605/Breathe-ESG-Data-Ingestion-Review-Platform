"""
URL Configuration for breathe.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from organizations.auth_views import login
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "status": "online",
        "message": "Breathe ESG API is running.",
        "endpoints": {
            "admin": "/admin/",
            "login": "/api/auth/login/",
            "refresh": "/api/auth/refresh/",
            "api": "/api/"
        }
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/auth/login/', login, name='login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Routes
    path('api/', include('api.urls')),
]
