from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsManager(permissions.BasePermission):
    """
    Allows access only to manager users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_manager())


class IsInventoryStaff(permissions.BasePermission):
    """
    Allows access only to inventory staff.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_inventory_staff())


class IsSalesStaff(permissions.BasePermission):
    """
    Allows access only to sales staff.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_sales_staff())


class IsAdminOrManager(permissions.BasePermission):
    """
    Allows access only to admin or manager users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_admin() or request.user.is_manager()))


class IsAdminOrManagerOrSalesStaff(permissions.BasePermission):
    """
    Allows access only to admin, manager or sales staff users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_admin() or request.user.is_manager() or request.user.is_sales_staff()))


class IsAdminOrManagerOrInventoryStaff(permissions.BasePermission):
    """
    Allows access only to admin, manager or inventory staff users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_admin() or request.user.is_manager() or request.user.is_inventory_staff()))


class IsOwner(permissions.BasePermission):
    """
    Allows access only to the owner of an object.
    """

    def has_object_permission(self, request, view, obj):
        # Assuming the object has either a 'user' or 'customer' field as the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        return False


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Allows access to the owner of an object or any staff member.
    """

    def has_object_permission(self, request, view, obj):
        # Staff members can access any object
        if request.user.is_admin() or request.user.is_manager() or \
                request.user.is_sales_staff() or request.user.is_inventory_staff():
            return True

        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        return False


class ReadOnly(permissions.BasePermission):
    """
    Allows read-only access to any authenticated user.
    """

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS and
            request.user and
            request.user.is_authenticated
        )
