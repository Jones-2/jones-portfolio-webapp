from django.contrib import admin

from django.contrib import admin
from .models import Post, PostTagMap


class PostTagInline(admin.TabularInline):
    model = PostTagMap
    extra = 1
    autocomplete_fields = ["tag"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "published_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at", "-created_at")
    date_hierarchy = "published_at"
    inlines = [PostTagInline]
