from django.urls import path, include
from django.contrib import admin
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="WhatsApp Bot API",
        default_version='v1',
        description="API para gerenciar o webhook do WhatsApp",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contato@minhaempresa.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url="https://6e7a-2804-d4b-8270-d800-d512-90eb-96e3-61bf.ngrok-free.app"
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('webhook.urls')),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
