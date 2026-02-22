from django.shortcuts import render
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
# Create your views here.
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

from common.models import PublishStatus  # or wherever your PublishStatus lives
from common.models import PublishStatus
from .models import Project
from .serializers import ProjectReadSerializer, ProjectWriteSerializer, ProjectSerializer
from .permissions import IsAdminOrReadOnly


class ProjectListView(ListAPIView):
    queryset = Project.objects.filter(status=PublishStatus.PUBLISHED).order_by("-published_at", "-created_at")
    serializer_class = ProjectSerializer
    authentication_classes = []
    permission_classes = []


class ProjectListView(ListAPIView):
    queryset = Project.objects.filter(status=PublishStatus.PUBLISHED)
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_featured"]
    ordering_fields = ["published_at", "created_at"]



class ProjectViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_fields = ["is_featured", "status", "industry"]
    ordering_fields = ["published_at", "created_at", "updated_at", "title"]
    search_fields = ["title", "summary", "content", "industry", "client_name"]

    def get_queryset(self):
        qs = Project.objects.all()

        # Public users only see published projects (and not confidential ones, if you want)
        user = self.request.user
        if not (user and user.is_staff):
            qs = qs.filter(status=PublishStatus.PUBLISHED, is_confidential=False)

        return qs.order_by("-published_at", "-created_at")

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return ProjectWriteSerializer
        return ProjectReadSerializer
