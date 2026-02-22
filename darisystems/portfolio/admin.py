from django.contrib import admin

from .models import (
    Project,
    Technology,
    ProjectTechnology,
    ProjectMedia,
    ProjectTagMap,
)

class ProjectTechnologyInline(admin.TabularInline):
    model = ProjectTechnology
    extra = 1
    autocomplete_fields = ["technology"]

class ProjectMediaInline(admin.TabularInline):
    model = ProjectMedia
    extra = 1

class ProjectTagMapInline(admin.TabularInline):
    model = ProjectTagMap
    extra = 1
    autocomplete_fields = ["tag"]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "is_featured", "is_confidential", "published_at", "updated_at")
    list_filter = ("status", "is_featured", "is_confidential", "industry")
    search_fields = ("title", "summary", "content", "industry", "client_name")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at", "-created_at")
    date_hierarchy = "published_at"

    inlines = [ProjectTechnologyInline, ProjectMediaInline, ProjectTagMapInline]

@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "updated_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    # enables autocomplete in the inline
    ordering = ("name",)

@admin.register(ProjectMedia)
class ProjectMediaAdmin(admin.ModelAdmin):
    list_display = ("project", "media_type", "display_order", "created_at")
    list_filter = ("media_type",)
    search_fields = ("project__title", "caption")
    ordering = ("project", "display_order")

@admin.register(ProjectTechnology)
class ProjectTechnologyAdmin(admin.ModelAdmin):
    list_display = ("project", "technology", "created_at")
    search_fields = ("project__title", "technology__name")

@admin.register(ProjectTagMap)
class ProjectTagMapAdmin(admin.ModelAdmin):
    list_display = ("project", "tag", "created_at")
    search_fields = ("project__title", "tag__name")
