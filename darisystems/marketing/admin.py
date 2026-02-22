from django.contrib import admin
from .models import ContactSubmission, Subscriber

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("full_name", "email", "subject", "message")
    ordering = ("-created_at",)

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "subscribed_at", "unsubscribed_at")
    list_filter = ("status",)
    search_fields = ("email",)
    ordering = ("-created_at",)

