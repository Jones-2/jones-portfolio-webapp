"""darisystems URL Configuration"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def root(request):
    return JsonResponse({
        "status": "ok",
        "message": "Dari Systems API is running",
        "docs": "/api/docs/",
        "schema": "/api/schema/",
    })

urlpatterns = [
    path("", root),
    path("admin/", admin.site.urls),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/", SpectacularAPIView.as_view(), name="schema-alias"),  # optional alias

    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include("api.urls")),
 ]

