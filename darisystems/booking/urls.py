from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ServiceViewSet,
    BookingRequestCreateView,
    BookingRequestPublicDetailView,
    BookingRequestAdminViewSet,
    AvailabilityRuleAdminViewSet,
    BlackoutPeriodAdminViewSet,
    AvailabilityPublicView,
)

router = DefaultRouter()
# clean: /api/v1/booking/services/
router.register(r"services", ServiceViewSet, basename="booking-services")

# admin routers
router.register(r"admin/requests", BookingRequestAdminViewSet, basename="booking-admin-requests")
router.register(r"admin/availability-rules", AvailabilityRuleAdminViewSet, basename="booking-admin-availability")
router.register(r"admin/blackouts", BlackoutPeriodAdminViewSet, basename="booking-admin-blackouts")

urlpatterns = [
    # public booking requests
    path("requests/", BookingRequestCreateView.as_view(), name="booking-request-create"),
    path("requests/<str:public_id>/", BookingRequestPublicDetailView.as_view(), name="booking-request-public"),
    # public availability
    path("availability/", AvailabilityPublicView.as_view(), name="booking-availability"),
]

urlpatterns += router.urls
