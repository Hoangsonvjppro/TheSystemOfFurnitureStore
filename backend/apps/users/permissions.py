from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với người dùng admin.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())


class IsManagerUser(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với người dùng quản lý (manager).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_manager())


class IsInventoryStaff(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với nhân viên kho.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_inventory_staff())


class IsSalesStaff(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với nhân viên bán hàng.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_sales_staff())


class IsAdminOrManager(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với admin hoặc quản lý.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_admin() or request.user.is_manager()))


class IsAdminOrManagerOrSalesStaff(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với admin, quản lý hoặc nhân viên bán hàng.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_admin() or request.user.is_manager() or request.user.is_sales_staff()))


class IsAdminOrManagerOrInventoryStaff(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với admin, quản lý hoặc nhân viên kho.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    (request.user.is_admin() or request.user.is_manager() or request.user.is_inventory_staff()))


class IsOwner(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với chủ sở hữu của đối tượng.
    """

    def has_object_permission(self, request, view, obj):
        # Giả định đối tượng có trường 'user' hoặc 'customer' là chủ sở hữu
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        return False


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Cho phép chủ sở hữu hoặc bất kỳ nhân viên nào truy cập đối tượng.
    """

    def has_object_permission(self, request, view, obj):
        # Nhân viên có thể truy cập bất kỳ đối tượng nào
        if request.user.is_admin() or request.user.is_manager() or \
                request.user.is_sales_staff() or request.user.is_inventory_staff():
            return True

        # Kiểm tra nếu user là chủ sở hữu
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        return False


class ReadOnly(permissions.BasePermission):
    """
    Chỉ cho phép truy cập đọc (read-only) với người dùng đã xác thực.
    """

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS and
            request.user and
            request.user.is_authenticated
        )


class IsBranchManager(permissions.BasePermission):
    """
    Chỉ cho phép quản lý chi nhánh truy cập dữ liệu chi nhánh của mình.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_manager())

    def has_object_permission(self, request, view, obj):
        # Cho phép nếu user là quản lý của chi nhánh
        if hasattr(obj, 'manager'):
            return obj.manager == request.user

        # Nếu đối tượng liên quan đến chi nhánh (ví dụ Stock), kiểm tra mối quan hệ đó
        if hasattr(obj, 'branch'):
            return obj.branch.manager == request.user

        return False


class IsBranchStaff(permissions.BasePermission):
    """
    Chỉ cho phép nhân viên truy cập dữ liệu của chi nhánh được phân công.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.branch is not None and
            (request.user.is_inventory_staff() or request.user.is_sales_staff())
        )

    def has_object_permission(self, request, view, obj):
        # Nhân viên chỉ được truy cập dữ liệu của chi nhánh mình
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch

        return False


class IsSalesOrManager(permissions.BasePermission):
    """
    Chỉ cho phép truy cập với nhân viên bán hàng hoặc quản lý.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.is_sales_staff() or request.user.is_manager()
        ))
