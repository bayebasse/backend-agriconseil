from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from .profile_serializers import ProfileSerializer


class ProfileView(APIView):
    authentication_classes = [
        TokenAuthentication
    ]

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        serializer = ProfileSerializer(
            request.user
        )

        return Response(
            serializer.data
        )

    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            ProfileSerializer(
                request.user
            ).data
        )