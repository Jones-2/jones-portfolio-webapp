
# Create your models here.
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from common.models import TimeStampedModel,TagScope, PublishStatus, _require_published_at_if_published


# Crea
# -----------------------------
class Post(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.CharField(max_length=500, blank=True, null=True)
    content = models.TextField()

    status = models.CharField(max_length=12, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    published_at = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField("common.Tag", through="PostTagMap", related_name="posts", blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["status", "published_at"], name="idx_post_status_pub"),
            models.Index(fields=["created_at"], name="idx_post_created"),
        ]

    def clean(self):
        _require_published_at_if_published(self)

    def __str__(self) -> str:
        return self.title


class PostTagMap(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey("common.Tag", on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "tag"], name="uq_post_tag"),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idy_content_ptm_tag"),
        ]

    def clean(self):
        if self.tag and self.tag.scope != TagScope.POST:
            raise ValidationError({"tag": "Tag scope must be POST for PostTagMap."})


