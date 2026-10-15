from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import RegionViewSet, DepartementViewSet, CommuneViewSet, CultureRefViewSet, CultureSuivieViewSet
from .prediction_views import YieldPredictionView, RecolteReelleListCreateView
from .buyer_views import BuyerCropCatalogView
router = DefaultRouter()
router.register("regions", RegionViewSet, basename="regions")
router.register("departements", DepartementViewSet, basename="departements")
router.register("communes", CommuneViewSet, basename="communes")
router.register("cultures", CultureRefViewSet, basename="cultures")
router.register("mes-cultures", CultureSuivieViewSet, basename="mes-cultures")
urlpatterns = [
    path("acheteur/cultures/", BuyerCropCatalogView.as_view(), name="buyer-crop-catalog"),
    path("mes-cultures/<int:culture_id>/prevision-rendement/", YieldPredictionView.as_view(), name="prevision-rendement"),
    path("mes-cultures/<int:culture_id>/recoltes-reelles/", RecolteReelleListCreateView.as_view(), name="recoltes-reelles"),
    path("", include(router.urls)),
]
