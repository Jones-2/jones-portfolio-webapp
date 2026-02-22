from django.db import models
from common.models import TimeStampedModel,TagScope, PublishStatus
from django.utils import timezone
# Create your models here.

# -----------------------------
# Contact & Newsletter
# -----------------------------
class ContactStatus(models.TextChoices):
    NEW = "NEW", "New"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    CLOSED = "CLOSED", "Closed"


class ContactSubmission(TimeStampedModel):
    full_name = models.CharField(max_length=160)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=12, choices=ContactStatus.choices, default=ContactStatus.NEW)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"], name="idx_contact_status_created"),
            models.Index(fields=["email", "created_at"], name="idx_contact_email_created"),
        ]


class SubscriberStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    UNSUBSCRIBED = "UNSUBSCRIBED", "Unsubscribed"


class Subscriber(TimeStampedModel):
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=12, choices=SubscriberStatus.choices, default=SubscriberStatus.ACTIVE)
    subscribed_at = models.DateTimeField(default=timezone.now)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="idx_subscriber_status"),
        ]

    def unsubscribe(self):
        self.status = SubscriberStatus.UNSUBSCRIBED
        self.unsubscribed_at = timezone.now()
        self.save()