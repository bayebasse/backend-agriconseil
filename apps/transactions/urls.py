from django.urls import path

from .views import OrderListCreateView, ReservationListCreateView, TransactionActionView


urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list"),
    path("crops/<int:culture_id>/orders/", OrderListCreateView.as_view(), name="order-create"),
    path("orders/<int:pk>/action/", TransactionActionView.as_view(), {"kind": "order"}, name="order-action"),
    path("reservations/", ReservationListCreateView.as_view(), name="reservation-list"),
    path("crops/<int:culture_id>/reservations/", ReservationListCreateView.as_view(), name="reservation-create"),
    path("reservations/<int:pk>/action/", TransactionActionView.as_view(), {"kind": "reservation"}, name="reservation-action"),
]
