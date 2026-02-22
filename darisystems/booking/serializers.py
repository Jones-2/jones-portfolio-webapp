from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from .models import (
    ConsultingService,
    ConsultingServiceStatus,
    BookingRequest,
    BookingStatus,
    MeetingMode,
    AvailabilityRule,
    BlackoutPeriod,
)

class ConsultingServiceReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultingService
        fields = [
            "id", "slug", "name", "description",
            "deliverables",
            "default_duration_minutes",
            "allowed_durations_minutes",
            "price_amount", "currency",
            "meeting_modes",
            "status",
            "created_at", "updated_at",
        ]

class ConsultingServiceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultingService
        fields = [
            "slug", "name", "description",
            "deliverables",
            "default_duration_minutes",
            "allowed_durations_minutes",
            "price_amount", "currency",
            "meeting_modes",
            "status",
        ]


class BookingRequestCreateSerializer(serializers.ModelSerializer):
    """
    Public create endpoint.
    Client submits:
      - service (slug)
      - requested_start_at
      - duration_minutes
      - meeting_mode
      - user details
    Server computes requested_end_at = start + duration.
    """
    service = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=ConsultingService.objects.all(),
    )

    class Meta:
        model = BookingRequest
        fields = [
            "service",
            "full_name", "email", "company", "role", "phone",
            "timezone",
            "duration_minutes",
            "requested_start_at",
            "meeting_mode",
            "problem_statement",
        ]

    def validate(self, attrs):
        service: ConsultingService = attrs["service"]

        if service.status != ConsultingServiceStatus.PUBLISHED:
            raise serializers.ValidationError({"service": "Service is not available for booking."})

        duration = attrs.get("duration_minutes") or service.default_duration_minutes
        if duration <= 0:
            raise serializers.ValidationError({"duration_minutes": "duration_minutes must be > 0."})

        allowed = service.allowed_durations_minutes
        if allowed and duration not in allowed:
            raise serializers.ValidationError({"duration_minutes": f"duration_minutes must be one of {allowed}."})

        meeting_mode = attrs.get("meeting_mode")
        if meeting_mode not in MeetingMode.values:
            raise serializers.ValidationError({"meeting_mode": "Invalid meeting mode."})

        meeting_modes_allowed = service.meeting_modes
        if meeting_modes_allowed and meeting_mode not in meeting_modes_allowed:
            raise serializers.ValidationError({"meeting_mode": f"meeting_mode must be one of {meeting_modes_allowed}."})

        start = attrs.get("requested_start_at")
        if not start:
            raise serializers.ValidationError({"requested_start_at": "requested_start_at is required."})

        # Optional: block requests in the past
        if start < timezone.now():
            raise serializers.ValidationError({"requested_start_at": "requested_start_at cannot be in the past."})

        attrs["duration_minutes"] = duration
        attrs["requested_end_at"] = start + timedelta(minutes=duration)
        return attrs

    def create(self, validated_data):
        # requested_end_at was injected in validate()
        end = validated_data.pop("requested_end_at")
        obj = BookingRequest.objects.create(**validated_data, requested_end_at=end)
        return obj


class BookingRequestPublicSerializer(serializers.ModelSerializer):
    service = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            "public_id",
            "service",
            "status",
            "full_name", "email", "company", "role", "phone",
            "timezone",
            "duration_minutes",
            "requested_start_at", "requested_end_at",
            "meeting_mode",
            "problem_statement",
            "meeting_url",
            "created_at", "updated_at",
            "confirmed_at", "cancelled_at",
        ]
        read_only_fields = fields


class BookingRequestAdminSerializer(serializers.ModelSerializer):
    service = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            "public_id",
            "service",
            "status",
            "full_name", "email", "company", "role", "phone",
            "timezone",
            "duration_minutes",
            "requested_start_at", "requested_end_at",
            "meeting_mode",
            "problem_statement",
            "admin_notes",
            "meeting_url",
            "handled_by", "handled_at",
            "confirmed_at", "cancelled_at",
            "created_at", "updated_at",
        ]


class BookingConfirmSerializer(serializers.Serializer):
    meeting_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)


class AvailabilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRule
        fields = [
            "id",
            "timezone",
            "day_of_week",
            "start_time_local",
            "end_time_local",
            "slot_granularity_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "max_bookings_per_day",
            "min_lead_time_minutes",
            "is_active",
            "created_at",
            "updated_at",
        ]


class BlackoutPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackoutPeriod
        fields = [
            "id",
            "start_at",
            "end_at",
            "reason",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]
