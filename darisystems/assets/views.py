from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import Asset, AssetStatus
from .serializers import AssetReadSerializer, AssetWriteSerializer
from .permissions import IsAdminOrReadOnly
from .filters import AssetFilter

class AssetViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"  # slug-based detail URLs

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = AssetFilter

    ordering_fields = ["published_at", "created_at", "updated_at", "title"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        qs = Asset.objects.all().prefetch_related("tags")
        user = self.request.user

        # public users: only published assets
        if not (user and user.is_staff):
            qs = qs.filter(status=AssetStatus.PUBLISHED)

        return qs.order_by("-published_at", "-created_at")

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return AssetWriteSerializer
        return AssetReadSerializer
