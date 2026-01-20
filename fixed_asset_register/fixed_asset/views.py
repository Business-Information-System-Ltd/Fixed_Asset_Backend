from django.shortcuts import render
from rest_framework import viewsets
from .models import *
from .serializers import *

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class GeneralLedgerViewSet(viewsets.ModelViewSet):
    queryset = GeneralLedger.objects.all()
    serializer_class = GeneralLedgerSerializer

class GLAllocationViewSet(viewsets.ModelViewSet):
    queryset = GLAllocation.objects.all()
    serializer_class = GLAllocationSerializer

class WorkInProgressViewSet(viewsets.ModelViewSet):
    queryset = WorkInProgress.objects.all()
    serializer_class = WorkInProgressSerializer

class WIPItemViewSet(viewsets.ModelViewSet):
    queryset = WIPItem.objects.all()
    serializer_class = WIPItemSerializer

class FixedAssetRegisterViewSet(viewsets.ModelViewSet):
    queryset = FixedAssetRegister.objects.all()
    serializer_class = FixedAssetRegisterSerializer

class DepreciationViewSet(viewsets.ModelViewSet):
    queryset = Depreciation.objects.all()
    serializer_class = DepreciationSerializer

class DepreciationEventViewSet(viewsets.ModelViewSet):
    queryset = DepreciationEvent.objects.all()
    serializer_class = DepreciationEventSerializer

class AssetPolicyViewSet(viewsets.ModelViewSet):
    queryset = AssetPolicy.objects.all()
    serializer_class = AssetPolicySerializer

class AssetDisposalViewSet(viewsets.ModelViewSet):
    queryset = AssetDisposal.objects.all()
    serializer_class = AssetDisposalSerializer

class AssetAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = AssetAdjustment.objects.all()
    serializer_class = AssetAdjustmentSerializer

class AssetDepartmentHistoryViewSet(viewsets.ModelViewSet):
    queryset = AssetDepartmentHistory.objects.all()
    serializer_class = AssetDepartmentHistorySerializer

