from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from common.models import TimeStampedModel



# -----------------------------
# Consultancy Booking
# -----------------------------
class ConsultingServiceStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


class MeetingMode(models.TextChoices):
    GOOGLE_MEET = "GOOGLE_MEET", "Google Meet"
    TEAMS = "TEAMS", "Microsoft Teams"
    ZOOM = "ZOOM", "Zoom"
    PHONE = "PHONE", "Phone"
    IN_PERSON = "IN_PERSON", "In-person"


class ConsultingService(TimeStampedModel):
    slug = models.SlugField(max_length=160, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    # Keep JSON as TextField if you want strict portability; Django supports JSONField on MySQL 5.7+.
    deliverables = models.JSONField(blank=True, null=True)
    default_duration_minutes = models.PositiveIntegerField(default=60)
    allowed_durations_minutes = models.JSONField(blank=True, null=True)

    price_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default="USD")
    meeting_modes = models.JSONField(blank=True, null=True)

    status = models.CharField(max_length=12, choices=ConsultingServiceStatus.choices, default=ConsultingServiceStatus.DRAFT)

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="idx_cs_status"),
        ]

    def __str__(self) -> str:
        return self.name


class BookingStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    CONFIRMED = "CONFIRMED", "Confirmed"
    DECLINED = "DECLINED", "Declined"
    CANCELLED_BY_REQUESTER = "CANCELLED_BY_REQUESTER", "Cancelled by requester"
    CANCELLED_BY_ADMIN = "CANCELLED_BY_ADMIN", "Cancelled by admin"
    COMPLETED = "COMPLETED", "Completed"


def generate_public_id(length: int = 12) -> str:
    # URL-safe token. 12 chars is fine for public lookup without being guessable.
    # (Not a cryptographic guarantee of uniqueness — DB unique constraint is the true guard.)
    return secrets.token_urlsafe(16).replace("-", "").replace("_", "")[:length]


class BookingRequest(TimeStampedModel):
    public_id = models.CharField(max_length=12, unique=True, default=generate_public_id, editable=False)

    service = models.ForeignKey(ConsultingService, on_delete=models.PROTECT, related_name="bookings")

    status = models.CharField(max_length=30, choices=BookingStatus.choices, default=BookingStatus.REQUESTED)

    full_name = models.CharField(max_length=160)
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True, null=True)
    role = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    timezone = models.CharField(max_length=64, default="UTC")
    duration_minutes = models.PositiveIntegerField()

    requested_start_at = models.DateTimeField()
    requested_end_at = models.DateTimeField()

    meeting_mode = models.CharField(max_length=20, choices=MeetingMode.choices)
    problem_statement = models.TextField(blank=True, null=True)

    admin_notes = models.TextField(blank=True, null=True)
    meeting_url = models.URLField(max_length=1024, blank=True, null=True)

    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="handled_bookings",
    )
    handled_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["service", "status", "requested_start_at"], name="idx_br_svc_status_time"),
            models.Index(fields=["email", "created_at"], name="idx_br_email_created"),
            models.Index(fields=["status", "requested_start_at"], name="idx_br_status_time"),
        ]

    def clean(self):
        if self.requested_start_at and self.requested_end_at and self.requested_start_at >= self.requested_end_at:
            raise ValidationError({"requested_end_at": "requested_end_at must be after requested_start_at."})

    def __str__(self) -> str:
        return f"{self.service.name} - {self.full_name} ({self.status})"

    @transaction.atomic
    def confirm(self, approved_by, meeting_url: Optional[str] = None) -> "BookingSlot":
        """
        Confirm this booking and create/lock a slot without overlaps.
        Transaction-safe overlap prevention using row locks + overlap query.
        """
        # Lock this booking row
        br = BookingRequest.objects.select_for_update().get(pk=self.pk)

        if br.status not in {BookingStatus.REQUESTED}:
            raise ValidationError(f"Booking cannot be confirmed from status {br.status}.")

        # Check for overlap with existing held/confirmed slots
        overlap = BookingSlot.objects.select_for_update().filter(
            status__in=[BookingSlotStatus.HELD, BookingSlotStatus.CONFIRMED],
        ).filter(
            Q(start_at__lt=br.requested_end_at) & Q(end_at__gt=br.requested_start_at)
        ).exists()

        if overlap:
            raise ValidationError("Requested time overlaps with an existing booking slot.")

        slot = BookingSlot.objects.create(
            booking_request=br,
            start_at=br.requested_start_at,
            end_at=br.requested_end_at,
            status=BookingSlotStatus.CONFIRMED,
        )

        br.status = BookingStatus.CONFIRMED
        br.handled_by = approved_by
        br.handled_at = timezone.now()
        br.confirmed_at = timezone.now()
        if meeting_url:
            br.meeting_url = meeting_url
        br.save()

        return slot

    @transaction.atomic
    def cancel(self, cancelled_by_admin: bool = False, actor=None):
        """
        Cancel booking and release slot if present.
        """
        br = BookingRequest.objects.select_for_update().get(pk=self.pk)
        if br.status in {BookingStatus.CANCELLED_BY_ADMIN, BookingStatus.CANCELLED_BY_REQUESTER, BookingStatus.DECLINED, BookingStatus.COMPLETED}:
            return

        br.status = BookingStatus.CANCELLED_BY_ADMIN if cancelled_by_admin else BookingStatus.CANCELLED_BY_REQUESTER
        br.cancelled_at = timezone.now()
        if actor:
            br.handled_by = actor
            br.handled_at = timezone.now()
        br.save()

        BookingSlot.objects.filter(booking_request=br).update(status=BookingSlotStatus.RELEASED, updated_at=timezone.now())


class BookingSlotStatus(models.TextChoices):
    HELD = "HELD", "Held"
    CONFIRMED = "CONFIRMED", "Confirmed"
    RELEASED = "RELEASED", "Released"


class BookingSlot(TimeStampedModel):
    booking_request = models.OneToOneField(BookingRequest, on_delete=models.CASCADE, related_name="slot")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=BookingSlotStatus.choices, default=BookingSlotStatus.CONFIRMED)
    hold_expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "start_at"], name="idx_bs_status_start"),
            models.Index(fields=["start_at", "end_at"], name="idx_bs_range"),
        ]

    def clean(self):
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError({"end_at": "end_at must be after start_at."})


class AvailabilityRule(TimeStampedModel):
    """
    Weekly availability windows in a given timezone.
    day_of_week: 0=Mon ... 6=Sun (your API can map accordingly)
    """
    timezone = models.CharField(max_length=64, default="UTC")
    day_of_week = models.PositiveSmallIntegerField()  # validate 0..6
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()

    slot_granularity_minutes = models.PositiveIntegerField(default=30)
    buffer_before_minutes = models.PositiveIntegerField(default=0)
    buffer_after_minutes = models.PositiveIntegerField(default=0)

    max_bookings_per_day = models.PositiveIntegerField(blank=True, null=True)
    min_lead_time_minutes = models.PositiveIntegerField(default=720)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["day_of_week", "is_active"], name="idx_ar_day_active"),
            models.Index(fields=["timezone"], name="idx_ar_tz"),
        ]

    def clean(self):
        if self.day_of_week > 6:
            raise ValidationError({"day_of_week": "day_of_week must be between 0 and 6."})
        if self.start_time_local and self.end_time_local and self.start_time_local >= self.end_time_local:
            raise ValidationError({"end_time_local": "end_time_local must be after start_time_local."})


class BlackoutPeriod(models.Model):
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    reason = models.CharField(max_length=200, blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["start_at", "end_at"], name="idx_blackout_range"),
        ]

    def clean(self):
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError({"end_at": "end_at must be after start_at."})


