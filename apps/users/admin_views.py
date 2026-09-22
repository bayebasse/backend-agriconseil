from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


from .admin_serializers import (
    AdminAddCultureSerializer,
    AdminCultureSummarySerializer,
    AdminFarmerSerializer,
)
from .permissions import IsAdminRole


User = get_user_model()


class AdminFarmerListCreateView(APIView):
    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        IsAdminRole,
    ]

    def get(self, request):
        farmers = (
            User.objects
            .filter(role="farmer")
            .prefetch_related(
                "cultures_suivies__culture",
                "cultures_suivies__region",
                "cultures_suivies__departement",
                "cultures_suivies__commune",
            )
            .order_by(
                "last_name",
                "first_name",
                "username",
            )
        )

        serializer = AdminFarmerSerializer(
            farmers,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = AdminFarmerSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        farmer = serializer.save()

        return Response(
            AdminFarmerSerializer(
                farmer
            ).data,
            status=status.HTTP_201_CREATED,
        )


class AdminFarmerDetailView(APIView):
    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        IsAdminRole,
    ]

    def get(self, request, pk):
        farmer = get_object_or_404(
            User,
            pk=pk,
            role="farmer",
        )

        serializer = AdminFarmerSerializer(
            farmer
        )

        return Response(serializer.data)

    def patch(self, request, pk):
        farmer = get_object_or_404(
            User,
            pk=pk,
            role="farmer",
        )

        serializer = AdminFarmerSerializer(
            farmer,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        farmer = serializer.save()

        return Response(
            AdminFarmerSerializer(
                farmer
            ).data
        )

    def delete(self, request, pk):
        farmer = get_object_or_404(
            User,
            pk=pk,
            role="farmer",
        )

        farmer.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class AdminFarmerCultureCreateView(APIView):
    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated,
        IsAdminRole,
    ]

    def post(self, request, pk):
        farmer = get_object_or_404(
            User,
            pk=pk,
            role="farmer",
        )

        serializer = AdminAddCultureSerializer(
            data=request.data,
            context={
                "farmer": farmer
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        culture = serializer.save()

        return Response(
            AdminCultureSummarySerializer(
                culture
            ).data,
            status=status.HTTP_201_CREATED,
        )