from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from common.models import PublishStatus
from .models import Post
from .serializers import PostReadSerializer, PostWriteSerializer
from .permissions import IsAdminOrReadOnly
from .filters import PostFilter

class PostViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"  # slug-based detail URLs

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = PostFilter
    ordering_fields = ["published_at", "created_at", "updated_at", "title"]
    search_fields = ["title", "excerpt", "content"]

    def get_queryset(self):
        qs = Post.objects.all().prefetch_related("tags")
        user = self.request.user
        if not (user and user.is_staff):
            qs = qs.filter(status=PublishStatus.PUBLISHED)
        return qs.order_by("-published_at", "-created_at")

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return PostWriteSerializer
        return PostReadSerializer
