"""Authentication and user-profile endpoints."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from drf_spectacular.utils import extend_schema

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    GitHubOAuthSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services.github_oauth import exchange_github_code, fetch_github_user


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — create a new account and return JWT tokens."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register a new account",
        responses={201: UserSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "data": {
                    "user": UserSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — authenticate and return JWT tokens + user profile."""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Login with email and password")
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "data": serializer.validated_data})


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the refresh token."""

    @extend_schema(summary="Logout and invalidate refresh token")
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"success": True, "data": {"message": "Logged out."}})
        except Exception:
            return Response(
                {"success": False, "error": {"code": "INVALID_TOKEN", "message": "Invalid token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/ — retrieve or update the current user's profile."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(summary="Get current user profile")
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(summary="Update current user profile")
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class GitHubOAuthView(APIView):
    """POST /api/auth/github/ — exchange GitHub OAuth code for access token and link account."""

    @extend_schema(
        summary="GitHub OAuth callback",
        request=GitHubOAuthSerializer,
    )
    def post(self, request):
        serializer = GitHubOAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        github_token = exchange_github_code(code)
        github_user = fetch_github_user(github_token)

        # Link GitHub account to the authenticated user
        user = request.user
        user.github_token = github_token
        user.github_username = github_user.get("login", "")
        user.github_avatar_url = github_user.get("avatar_url", "")
        user.save(update_fields=["github_token", "github_username", "github_avatar_url"])

        return Response(
            {"success": True, "data": UserSerializer(user).data}
        )
