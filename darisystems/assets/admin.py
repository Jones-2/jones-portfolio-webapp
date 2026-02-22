from django.contrib import admin
from .models import Asset, AssetTagMap

class AssetTagInline(admin.TabularInline):
    model = AssetTagMap
    extra = 1
    autocomplete_fields = ["tag"]

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("title", "asset_type", "status", "is_featured", "published_at", "updated_at")
    list_filter = ("asset_type", "status", "is_featured")
    search_fields = ("title", "description", "external_url", "download_url")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at", "-created_at")
    date_hierarchy = "published_at"
    inlines = [AssetTagInline]

@admin.register(AssetTagMap)
class AssetTagMapAdmin(admin.ModelAdmin):
    list_display = ("asset", "tag", "created_at")
    search_fields = ("asset__title", "tag__name", "tag__slug")

