import django_filters
from .models import ContactSubmission, Subscriber

class ContactSubmissionFilter(django_filters.FilterSet):
    class Meta:
        model = ContactSubmission
        fields = ["status", "email"]

class SubscriberFilter(django_filters.FilterSet):
    class Meta:
        model = Subscriber
        fields = ["status", "email"]
