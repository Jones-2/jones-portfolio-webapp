from django.contrib import admin
from .models import (
    ConsultingService,
    BookingRequest,
    BookingSlot,
    AvailabilityRule,
    BlackoutPeriod,
)

@admin.register(ConsultingService)
class ConsultingServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "default_duration_minutes", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("public_id", "service", "full_name", "email", "status", "requested_start_at", "created_at")
    list_filter = ("status", "meeting_mode", "service")
    search_fields = ("public_id", "full_name", "email", "company", "problem_statement", "admin_notes")
    ordering = ("-created_at",)

@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin):
    list_display = ("booking_request", "status", "start_at", "end_at", "hold_expires_at")
    list_filter = ("status",)
    ordering = ("-start_at",)

@admin.register(AvailabilityRule)
class AvailabilityRuleAdmin(admin.ModelAdmin):
    list_display = ("timezone", "day_of_week", "start_time_local", "end_time_local", "slot_granularity_minutes", "is_active")
    list_filter = ("timezone", "day_of_week", "is_active")
    ordering = ("day_of_week", "start_time_local")

@admin.register(BlackoutPeriod)
class BlackoutPeriodAdmin(admin.ModelAdmin):
    list_display = ("start_at", "end_at", "reason", "created_by", "created_at")
    search_fields = ("reason",)
    ordering = ("-start_at",)
