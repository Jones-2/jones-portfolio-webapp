import django_filters
from .models import Asset

class AssetFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method="filter_tag")

    class Meta:
        model = Asset
        fields = ["tag", "asset_type", "status", "is_featured"]

    def filter_tag(self, queryset, name, value):
        # filter assets that have a tag with this slug
        return queryset.filter(tags__slug=value)
