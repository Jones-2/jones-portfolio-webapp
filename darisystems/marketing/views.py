from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import ContactSubmission, Subscriber, SubscriberStatus
from .serializers import (
    ContactSubmissionCreateSerializer,
    ContactSubmissionAdminSerializer,
    SubscribeSerializer,
    UnsubscribeSerializer,
    SubscriberAdminSerializer,
)
from .permissions import IsAdminUser
from .filters import ContactSubmissionFilter, SubscriberFilter


# ----------------------------
# Public endpoints
# ----------------------------
class ContactSubmissionCreateView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ContactSubmissionCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = ContactSubmission.objects.create(**serializer.validated_data)
        return Response({"id": obj.id, "status": obj.status}, status=status.HTTP_201_CREATED)


class SubscribeView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SubscribeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        sub, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={"status": SubscriberStatus.ACTIVE},
        )
        if not created and sub.status != SubscriberStatus.ACTIVE:
            sub.status = SubscriberStatus.ACTIVE
            sub.unsubscribed_at = None
            sub.save()

        return Response({"email": sub.email, "status": sub.status}, status=status.HTTP_200_OK)


class UnsubscribeView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UnsubscribeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        try:
            sub = Subscriber.objects.get(email=email)
        except Subscriber.DoesNotExist:
            # Don’t leak whether the email exists
            return Response(
                {"detail": "If the email exists, it has been unsubscribed."},
                status=status.HTTP_200_OK,
            )

        sub.unsubscribe()
        return Response({"detail": "Unsubscribed."}, status=status.HTTP_200_OK)


# ----------------------------
# Admin endpoints
# ----------------------------
class ContactSubmissionAdminViewSet(ModelViewSet):
    queryset = ContactSubmission.objects.all().order_by("-created_at")
    serializer_class = ContactSubmissionAdminSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ContactSubmissionFilter
    ordering_fields = ["created_at", "updated_at", "status"]
    search_fields = ["full_name", "email", "subject", "message"]


class SubscriberAdminViewSet(ModelViewSet):
    queryset = Subscriber.objects.all().order_by("-created_at")
    serializer_class = SubscriberAdminSerializer
    permission_classes = [IsAdminUser]

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = SubscriberFilter
    ordering_fields = ["created_at", "updated_at", "status", "subscribed_at"]
    search_fields = ["email"]
