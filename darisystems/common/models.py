
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


# -----------------------------
# Base
# -----------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)


class PublishStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


def _require_published_at_if_published(instance: models.Model, status_field: str = "status", published_at_field: str = "published_at"):
    status = getattr(instance, status_field, None)
    published_at = getattr(instance, published_at_field, None)
    if status == PublishStatus.PUBLISHED and not published_at:
        raise ValidationError({published_at_field: "published_at is required when status is PUBLISHED."})


# -----------------------------
# Tags
# -----------------------------
class TagScope(models.TextChoices):
    POST = "POST", "Post"
    PROJECT = "PROJECT", "Project"
    ASSET = "ASSET", "Asset"

class Tag(TimeStampedModel):
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=80)
    scope = models.CharField(max_length=10, choices=TagScope.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["scope", "slug"], name="uq_tag_scope_slug"),
        ]
        indexes = [
            models.Index(fields=["scope"], name="idx_tag_scope"),
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.name}"

