import django_filters
from .models import Post

class PostFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method="filter_tag")

    class Meta:
        model = Post
        fields = ["tag"]

    def filter_tag(self, queryset, name, value):
        return queryset.filter(tags__slug=value)
