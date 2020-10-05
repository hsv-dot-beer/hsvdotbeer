from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    """
    Permissions for the user model:

    1. Admins can do everything
    2. Normal users can only read/write themselves
    """

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        if request.method == "POST" and "subscribe" in request.path:
            return True
        return request.method in permissions.SAFE_METHODS + ("PUT", "PATCH")

    def has_object_permission(self, request, view, obj):

        if request.user == obj:
            print("user matches")
            return True
        if request.user.is_staff:
            print("user is staff")
            return True

        print("fall through")
        return request.method in permissions.SAFE_METHODS
