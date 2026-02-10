from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views import DepreciationCalculationAPI
from .views import google_login

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
router.register(r'roles', RoleViewSet)

urlpatterns = [
    path('depreciation/calculate/', DepreciationCalculationAPI.as_view(), name='depreciation-calculation'),
    path('execute-depreciation/', ExecuteDepreciationAPI.as_view(), name='execute-depreciation'),
    path('fixed-assets/<int:pk>/full-detail/', FixedAssetFullDetailAPI.as_view(), name='fixed-asset-full-detail'),
    path('wips/<int:pk>/items/', WIPItemsAPI.as_view()),
    path('wips/<int:pk>/fixed-assets/', WIPFixedAssetAPI.as_view()),
    path('gl-allocations/<int:pk>/wips/', GLAllocationWIPAPI.as_view()),
    path('general-ledgers/<int:pk>/gl-allocations/', GLAllocationsByGLAPI.as_view()),
    path('companies/<int:pk>/departments/', CompanyDepartmentsAPI.as_view()),
    path('companies/<int:pk>/asset-policies/', CompanyAssetPolicyAPI.as_view()),
    path('departments/<int:pk>/asset-dept-histories/', DepartmentAssetDeptHistoryAPI.as_view()),
    path('departments/<int:pk>/asset-policies/',DepartmentAssetPolicyAPI.as_view()),
    path('accounts/<int:pk>/fixed-assets/',AccountFixedAssetAPI.as_view()),
    path('accounts/<int:pk>/depreciations/',AccountDepreciationAPI.as_view()),
    path('accounts/<int:pk>/general-ledgers/',AccountGeneralLedgerAPI.as_view()),
    path('asset-policies/<int:pk>/disposals/',AssetPolicyDisposalAPI.as_view()),
    path('asset-policies/<int:pk>/depreciation-events/',AssetPolicyDepreciationEventAPI.as_view()),
    path('asset-policies/<int:pk>/disposals/',AssetPolicyDisposalAPI.as_view()),
    path('depreciations/<int:pk>/depreciation-events/',DepreciationDepreEventAPI.as_view()),
    path('depreciations/<int:pk>/asset-policies/',DepreciationAssetPolicyAPI.as_view()),
    path('fixed-assets/<int:pk>/depreciation-events/',FixedAssetDepreciationEventAPI.as_view()),
    path('fixed-assets/<int:pk>/depreciations/',FixedAssetDepreciationAPI.as_view()),
    path('fixed-assets/<int:pk>/asset-policies/',FixedAssetPolicyAPI.as_view()),
    path('fixed-assets/<int:pk>/asset-adjustments/',FixedAssetAdjustmentAPI.as_view()),
    path('fixed-assets/<int:pk>/dept-histories/',FixedAssetDeptHistoryAPI.as_view()),
    path('fixed-assets/<int:pk>/asset-disposals/',FixedAssetDisposalAPI.as_view()),
    path('fixed-assets/<int:pk>/asset-components/',FixedAssetComponentAPI.as_view()),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('google-login/', google_login, name='google_login'),
    path('microsoft-login/', microsoft_login, name='microsoft_login'),

    path('', include(router.urls)),
    
]