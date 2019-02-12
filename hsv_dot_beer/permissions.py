from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # if the user is a staff user (i.e. can log into the admin page),
        # they can do anything in the API.
        # Otherwise, only let safe requests (e.g. GET, OPTIONS) through
        return user.is_staff or request.method in SAFE_METHODS
