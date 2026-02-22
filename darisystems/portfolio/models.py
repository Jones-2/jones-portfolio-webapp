
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



# -----------------------------
# Portfolio
# -----------------------------
class Project(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.CharField(max_length=500, blank=True, null=True)
    content = models.TextField()  # longform write-up (markdown/html)
    problem_statement = models.TextField(blank=True, null=True)
    solution_overview = models.TextField(blank=True, null=True)
    impact = models.TextField(blank=True, null=True)
    client_name = models.CharField(max_length=200, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)

    is_confidential = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    status = models.CharField(max_length=12, choices=PublishStatus.choices, default=PublishStatus.DRAFT)
    published_at = models.DateTimeField(blank=True, null=True)

    technologies = models.ManyToManyField("Technology", through="ProjectTechnology", related_name="projects", blank=True)
    tags = models.ManyToManyField("common.Tag", through="ProjectTagMap", related_name="projects", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "published_at"], name="idx_project_status_pub"),
            models.Index(fields=["is_featured", "published_at"], name="idx_project_featured"),
            models.Index(fields=["created_at"], name="idx_project_created"),
        ]

    def clean(self):
        TimeStampedModel._require_published_at_if_published(self)

    def __str__(self) -> str:
        return self.title


class Technology(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class ProjectTechnology(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    technology = models.ForeignKey(Technology, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "technology"], name="uq_project_technology"),
        ]
        indexes = [
            models.Index(fields=["technology"], name="idx_pt_technology"),
        ]


class ProjectMediaType(models.TextChoices):
    IMAGE = "IMAGE", "Image"
    VIDEO = "VIDEO", "Video"
    PDF = "PDF", "PDF"


class ProjectMedia(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=ProjectMediaType.choices, default=ProjectMediaType.IMAGE)
    file_url = models.URLField(max_length=1024)
    caption = models.CharField(max_length=255, blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["project", "display_order"], name="idx_pm_project_order"),
            models.Index(fields=["project"], name="idx_pm_project"),
        ]


class ProjectTagMap(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tag = models.ForeignKey("common.Tag", on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "tag"], name="uq_project_tag"),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idx_prtm_tag"),
        ]

    def clean(self):
        if self.tag and self.tag.scope != TagScope.PROJECT:
            raise ValidationError({"tag": "Tag scope must be PROJECT for ProjectTagMap."})


