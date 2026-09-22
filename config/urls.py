from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.users.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.cultures.urls")),
    path("api/", include("apps.calendrier.urls")),
    path("api/", include("apps.meteo.urls")),
    path("api/", include("apps.hydrique.urls")),
    path("api/", include("apps.ia.urls")),
    path(
    "api/admin/",
    include("apps.users.admin_urls"),
),
path(
    "api/auth/profile/",
    include("apps.users.profile_urls"),
),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
