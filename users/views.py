from django.contrib.auth.models import User
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer
from .models import UserProfile
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from drf_yasg.utils import swagger_auto_schema

@swagger_auto_schema(
    operation_summary="Register a new user",
    operation_description="Create a new user account. Returns user data upon successful registration.",
    responses={201: UserSerializer()}
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Retrieve the profile information for the currently authenticated user.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description="Update the profile for the currently authenticated user. Supports partial updates and avatar upload.",
        request_body=UserSerializer
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

@swagger_auto_schema(
    operation_summary="Obtain JWT token pair",
    operation_description="Submit username and password to receive an access and refresh token.",
)
class MyTokenObtainPairView(TokenObtainPairView):
    # You can customize the token claims here if needed
    pass

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change user password",
        operation_description="Allows an authenticated user to change their password by providing their old password and a new one.",
        request_body=ChangePasswordSerializer,
        responses={
            200: '{"success": "Password changed successfully."}',
            400: '{"error": "Invalid data."}'
        }
    )
    def post(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            form = PasswordChangeForm(user, serializer.data)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                return Response({'success': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete user account",
        operation_description="Permanently delete the account of the currently authenticated user. This action cannot be undone.",
        responses={204: "Account deleted successfully."}
    )
    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'success': 'Account deleted.'}, status=status.HTTP_204_NO_CONTENT)
