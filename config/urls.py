"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path

from django.conf import settings
from django.conf.urls.static import static
from users.jwt_serializers import CustomTokenObtainPairView

# JWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Swagger
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Настройка Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="ForWork API",
        default_version='v1',
        description="ERP-система для управления задачами, складом и персоналом",
        contact=openapi.Contact(email="kos26193@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('manufacturers.urls')),
    path('api/', include('banks.urls')),
    path('api/', include('documents.urls')),
    path('api/', include('counterparties.urls')),
    path('api/', include('categories.urls')),
    path('api/', include('inventory_categories.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('warehouse.urls')),
    path('api/', include('tasks.urls')),
    path('api/', include('chat.urls')),
    path('api/', include('notifications.urls')),
    path('api/gallery/', include('gallery.urls')),

    # JWT эндпоинты
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Swagger документация
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('', include('frontend.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # для логина/логаута
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)