from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.constants import Roles
from apps.branches.models import Branch
from apps.branches.serializers import BranchSerializer
from apps.common.permissions import ActionPermissionsMixin, role_required


class BranchViewSet(ActionPermissionsMixin, ModelViewSet):
    """Справочник филиалов: чтение — всем сотрудникам, изменение — ADMIN/MANAGER."""

    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    filterset_fields = ('city', 'is_active')
    search_fields = ('name', 'code', 'city')
    ordering_fields = ('name', 'city', 'created_at')

    permission_classes_by_action = {
        '__default__': (IsAuthenticated,),
        'create': (role_required(Roles.ADMIN, Roles.MANAGER),),
        'partial_update': (role_required(Roles.ADMIN, Roles.MANAGER),),
        'destroy': (role_required(Roles.ADMIN, Roles.MANAGER),),
    }
