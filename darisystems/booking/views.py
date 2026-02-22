from django.shortcuts import render

# Create your views here.
from datetime import datetime, timedelta
from django.utils import timezone as dj_tz
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    ConsultingService, ConsultingServiceStatus,
    BookingRequest, BookingStatus,
    AvailabilityRule, BlackoutPeriod,
)
from .serializers import (
    ConsultingServiceReadSerializer, ConsultingServiceWriteSerializer,
    BookingRequestCreateSerializer, BookingRequestPublicSerializer, BookingRequestAdminSerializer,
    BookingConfirmSerializer,
    AvailabilityRuleSerializer, BlackoutPeriodSerializer,
)
from .permissions import IsAdminUser, IsAdminOrReadOnly
from .filters import ConsultingServiceFilter, BookingRequestFilter


# ----------------------------
# Services
# ----------------------------
class ServiceViewSet(ModelViewSet):
    """
    Public: GET list/retrieve shows only PUBLISHED.
    Admin: full CRUD.
    """
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ConsultingServiceFilter
    ordering_fields = ["created_at", "updated_at", "name"]
    search_fields = ["name", "description"]

    def get_queryset(self):
        qs = ConsultingService.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(status=ConsultingServiceStatus.PUBLISHED)
        return qs.order_by("name")

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return ConsultingServiceWriteSerializer
        return ConsultingServiceReadSerializer


# ----------------------------
# Public booking requests
# ----------------------------
class BookingRequestCreateView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = BookingRequestCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        br = serializer.save()
        return Response(BookingRequestPublicSerializer(br).data, status=status.HTTP_201_CREATED)


class BookingRequestPublicDetailView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, public_id: str):
        br = BookingRequest.objects.filter(public_id=public_id).select_related("service").first()
        if not br:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(BookingRequestPublicSerializer(br).data, status=status.HTTP_200_OK)

    def post(self, request, public_id: str):
        """
        Public cancel endpoint (requester).
        """
        br = BookingRequest.objects.filter(public_id=public_id).first()
        if not br:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        br.cancel(cancelled_by_admin=False, actor=None)
        br.refresh_from_db()
        return Response(BookingRequestPublicSerializer(br).data, status=status.HTTP_200_OK)


# ----------------------------
# Admin booking requests
# ----------------------------
class BookingRequestAdminViewSet(ReadOnlyModelViewSet):
    queryset = BookingRequest.objects.all().select_related("service").order_by("-created_at")
    serializer_class = BookingRequestAdminSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "public_id"

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = BookingRequestFilter
    ordering_fields = ["created_at", "requested_start_at", "status"]
    search_fields = ["full_name", "email", "company", "role", "problem_statement", "admin_notes"]

    @action(detail=True, methods=["patch"], url_path="confirm")
    def confirm(self, request, public_id=None):
        br = self.get_object()
        ser = BookingConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        meeting_url = ser.validated_data.get("meeting_url") or None

        try:
            br.confirm(approved_by=request.user, meeting_url=meeting_url)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        br.refresh_from_db()
        return Response(BookingRequestAdminSerializer(br).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="decline")
    def decline(self, request, public_id=None):
        br = self.get_object()
        if br.status != BookingStatus.REQUESTED:
            return Response({"detail": f"Cannot decline from {br.status}."}, status=status.HTTP_400_BAD_REQUEST)

        br.status = BookingStatus.DECLINED
        br.handled_by = request.user
        br.handled_at = dj_tz.now()
        br.save()
        return Response(BookingRequestAdminSerializer(br).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel(self, request, public_id=None):
        br = self.get_object()
        br.cancel(cancelled_by_admin=True, actor=request.user)
        br.refresh_from_db()
        return Response(BookingRequestAdminSerializer(br).data, status=status.HTTP_200_OK)


# ----------------------------
# Availability & blackouts (admin CRUD)
# ----------------------------
class AvailabilityRuleAdminViewSet(ModelViewSet):
    queryset = AvailabilityRule.objects.all().order_by("day_of_week", "start_time_local")
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [IsAdminUser]


class BlackoutPeriodAdminViewSet(ModelViewSet):
    queryset = BlackoutPeriod.objects.all().order_by("-start_at")
    serializer_class = BlackoutPeriodSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ----------------------------
# Public availability endpoint (optional but useful)
# ----------------------------
class AvailabilityPublicView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        GET /api/v1/booking/availability/?start=2026-02-22&days=14
        Returns a simple list of blocked ranges (blackouts + confirmed slots)
        V1 lightweight (frontend can build UI).
        """
        start_str = request.query_params.get("start")
        days = int(request.query_params.get("days", "14"))

        if not start_str:
            return Response({"detail": "start is required (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "start must be YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        start_dt = dj_tz.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_dt = start_dt + timedelta(days=days)

        # Blackouts
        blackouts = list(
            BlackoutPeriod.objects.filter(start_at__lt=end_dt, end_at__gt=start_dt)
            .values("start_at", "end_at", "reason")
        )

        # Confirmed slots block time
        slots = list(
            BookingRequest.objects.filter(
                status=BookingStatus.CONFIRMED,
                requested_start_at__lt=end_dt,
                requested_end_at__gt=start_dt,
            ).values("requested_start_at", "requested_end_at")
        )

        return Response(
            {
                "range": {"start": start_dt, "end": end_dt},
                "blackouts": blackouts,
                "confirmed": slots,
            },
            status=status.HTTP_200_OK,
        )
