from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ContactSubmissionCreateView,
    SubscribeView,
    UnsubscribeView,
    ContactSubmissionAdminViewSet,
    SubscriberAdminViewSet,
)

router = DefaultRouter()
router.register(r"admin/contacts", ContactSubmissionAdminViewSet, basename="marketing-admin-contacts")
router.register(r"admin/subscribers", SubscriberAdminViewSet, basename="marketing-admin-subscribers")

urlpatterns = [
    path("contact/", ContactSubmissionCreateView.as_view(), name="marketing-contact"),
    path("subscribe/", SubscribeView.as_view(), name="marketing-subscribe"),
    path("unsubscribe/", UnsubscribeView.as_view(), name="marketing-unsubscribe"),
]

urlpatterns += router.urls
