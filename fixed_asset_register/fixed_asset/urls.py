from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'general-ledgers', GeneralLedgerViewSet)
router.register(r'gl-allocations',GLAllocationViewSet)
router.register(r'wips', WorkInProgressViewSet)
router.register(r'wip-items', WIPItemViewSet)
router.register(r'fixed-assets', FixedAssetRegisterViewSet)
router.register(r'asset-components', AssetComponentViewSet)
router.register(r'depreciations', DepreciationViewSet)
router.register(r'depreciation-events', DepreciationEventViewSet)
router.register(r'asset-policies', AssetPolicyViewSet)
router.register(r'asset-disposals', AssetDisposalViewSet)
router.register(r'asset-adjustments', AssetAdjustmentViewSet)
router.register(r'asset-dept-histories', AssetDepartmentHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]