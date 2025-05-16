from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsManagerUser(permissions.BasePermission):
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


class IsBranchManager(permissions.BasePermission):
    """
    Allows branch managers to access their own branch data
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_manager())

    def has_object_permission(self, request, view, obj):
        # Allow if user is the branch manager
        if hasattr(obj, 'manager'):
            return obj.manager == request.user

        # If object is related to a branch (like Stock), check that relationship
        if hasattr(obj, 'branch'):
            return obj.branch.manager == request.user

        return False


class IsBranchStaff(permissions.BasePermission):
    """
    Allows staff to access only their assigned branch data
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.branch is not None and
            (request.user.is_inventory_staff() or request.user.is_sales_staff())
        )

    def has_object_permission(self, request, view, obj):
        # Staff can access data for their branch
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch

        return False
