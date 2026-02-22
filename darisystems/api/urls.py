from django.urls import path, include

urlpatterns = [
    path("portfolio/", include("portfolio.urls")),
    path("content/", include("content.urls")),
    path("assets/", include("assets.urls")),
    path("marketing/", include("marketing.urls")),
    path("booking/", include("booking.urls")),
]
