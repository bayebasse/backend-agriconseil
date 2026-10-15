from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )


class IsBuyerRole(BasePermission):
    message = "Accès réservé aux acheteurs."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "buyer"
        )


class IsFarmerRole(BasePermission):
    message = "Accès réservé aux agriculteurs."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "farmer"
        )
