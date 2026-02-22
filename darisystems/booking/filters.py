import django_filters
from .models import BookingRequest, ConsultingService, BookingStatus

class ConsultingServiceFilter(django_filters.FilterSet):
    class Meta:
        model = ConsultingService
        fields = ["status"]

class BookingRequestFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    email = django_filters.CharFilter(field_name="email", lookup_expr="iexact")
    service = django_filters.CharFilter(field_name="service__slug", lookup_expr="iexact")
    start_from = django_filters.IsoDateTimeFilter(field_name="requested_start_at", lookup_expr="gte")
    start_to = django_filters.IsoDateTimeFilter(field_name="requested_start_at", lookup_expr="lte")

    class Meta:
        model = BookingRequest
        fields = ["status", "email", "service", "start_from", "start_to"]
