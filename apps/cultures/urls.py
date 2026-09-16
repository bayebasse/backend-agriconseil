from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import RegionViewSet, DepartementViewSet, CommuneViewSet, CultureRefViewSet, CultureSuivieViewSet
router = DefaultRouter()
router.register("regions", RegionViewSet, basename="regions")
router.register("departements", DepartementViewSet, basename="departements")
router.register("communes", CommuneViewSet, basename="communes")
router.register("cultures", CultureRefViewSet, basename="cultures")
router.register("mes-cultures", CultureSuivieViewSet, basename="mes-cultures")
urlpatterns = [path("", include(router.urls))]
