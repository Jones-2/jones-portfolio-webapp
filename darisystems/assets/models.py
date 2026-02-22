from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from common.models import TimeStampedModel,TagScope, PublishStatus



# Create your models here.

# -----------------------------
# Digital Assets
# -----------------------------
class AssetType(models.TextChoices):
    TOOL = "TOOL", "Tool"
    TEMPLATE = "TEMPLATE", "Template"
    GUIDE = "GUIDE", "Guide"
    LINK = "LINK", "Link"


class AssetStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    COMING_SOON = "COMING_SOON", "Coming soon"
    ARCHIVED = "ARCHIVED", "Archived"


class Asset(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True, null=True)
    asset_type = models.CharField(max_length=12, choices=AssetType.choices)
    status = models.CharField(max_length=12, choices=AssetStatus.choices, default=AssetStatus.DRAFT)
    external_url = models.URLField(max_length=1024, blank=True, null=True)
    download_url = models.URLField(max_length=1024, blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField("common.Tag", through="AssetTagMap", related_name="assets", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "published_at"], name="idx_asset_status_pub"),
            models.Index(fields=["asset_type"], name="idx_asset_type"),
            models.Index(fields=["is_featured", "published_at"], name="idx_asset_featured"),
        ]

    def clean(self):
        if self.status == AssetStatus.PUBLISHED and not self.published_at:
            raise ValidationError({"published_at": "published_at is required when status is PUBLISHED."})
        if self.asset_type == AssetType.LINK and not self.external_url:
            raise ValidationError({"external_url": "external_url is required for LINK assets."})

    def __str__(self) -> str:
        return self.title


class AssetTagMap(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    tag = models.ForeignKey("common.Tag", on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asset", "tag"], name="uq_asset_tag"),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idx_atm_tag"),
        ]

    def clean(self):
        if self.tag and self.tag.scope != TagScope.ASSET:
            raise ValidationError({"tag": "Tag scope must be ASSET for AssetTagMap."})

