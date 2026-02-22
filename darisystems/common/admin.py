from django.contrib import admin

from .models import Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "scope", "slug", "updated_at")
    list_filter = ("scope",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
