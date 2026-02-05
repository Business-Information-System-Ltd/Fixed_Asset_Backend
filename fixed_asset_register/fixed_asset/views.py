from django.shortcuts import render
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404
import traceback
from .services.depreciation import (
    get_total_units,
    get_elapsed_units,
    straight_line,
    reducing_balance,
    double_declining
)

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

class AssetComponentViewSet(viewsets.ModelViewSet):
    queryset = AssetComponent.objects.all()
    serializer_class = AssetComponentSerializer

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


class DepreciationCalculationAPI(APIView):
    def post(self, request):
        try:
            data = request.data
            method = data.get("depreciation_method")
            total_amount = Decimal(data.get("total_amount") or 0)
            residual_value = Decimal(data.get("residual_value") or 0)
            useful_life = int(data.get("useful_life") or 0)
            period = data.get("period")
            computation = data.get("computaion")
            capitalization_date_str = data.get("capitalization_date")
            capitalization_date = None
            if capitalization_date_str:
                capitalization_date = datetime.strptime(capitalization_date_str, "%Y-%m-%d").date()


            total_units = get_total_units(useful_life, period, computation)
            elapsed_units = get_elapsed_units(capitalization_date, computation)
            elapsed_units = min(elapsed_units, total_units)

            if method == "Straight Line":
                accumulated = straight_line(total_amount, residual_value, total_units, elapsed_units)
            elif method == "Reducing Balance":
                accumulated = reducing_balance(total_amount, residual_value, useful_life, elapsed_units, computation.upper())
            else:
                accumulated = double_declining(total_amount, residual_value, useful_life, elapsed_units, computation.upper())

            current_nbv = max(total_amount - accumulated, residual_value)

            return Response({
                "depreciation_method": method,
                "total_units": total_units,
                "elapsed_units": elapsed_units,
                "accumulated_depreciation": round(accumulated, 2),
                "current_nbv": round(current_nbv, 2),
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        return Response({"detail": "Use POST to calculate depreciation"}, status=200)

class FixedAssetFullDetailAPI(APIView):
    def get(self, request, pk):
        asset = get_object_or_404(
            FixedAssetRegister.objects.prefetch_related(
                'asset_components',
                'depreciation_set',
                'depreciationevent_set',
                'assetdisposal_set',
                'assetadjustment_set',
                'assetdepartmenthistory_set'

            ),
            pk=pk
        )  

        serializer = FixedAssetFullSerializer(asset)
        return Response(serializer.data, status=status.HTTP_200_OK)  


class WIPItemsAPI(APIView):
    def get(self, request, pk):
        wip_items = WIPItem.objects.filter(wip_id =pk)
        serializer = WIPItemSerializer(wip_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class WIPFixedAssetAPI(APIView):
    def get(self, request, pk):
        wip = get_object_or_404(WorkInProgress, pk=pk)
        fixed_assets = FixedAssetRegister.objects.filter(wip_id = pk)
        serializer = FixedAssetRegisterSerializer(fixed_assets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GLAllocationsByGLAPI(APIView):
    def get(self, request, pk):
        gl_allocations = GLAllocation.objects.filter(gl_id=pk)
        serializer = GLAllocationSerializer(gl_allocations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GLAllocationWIPAPI(APIView):
    def get(self, request, pk):
        gl_allocation = get_object_or_404(GLAllocation, pk=pk)
        wips = WorkInProgress.objects.filter(gl_allocation_id=pk)
        serializer = WorkInProgressSerializer(wips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
   
class CompanyDepartmentsAPI(APIView):
    def get(self, request, pk):
        departments = Department.objects.filter(company_id=pk)
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CompanyAssetPolicyAPI(APIView):
    def get(self, request, pk):
        asset_policies = AssetPolicy.objects.filter(company_id=pk)
        serializer = AssetPolicySerializer(asset_policies, many =True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DepartmentAssetDeptHistoryAPI(APIView):
    def get(self,request, pk):
        asset_dept_history = AssetDepartmentHistory.objects.filter(department_id =pk)
        serializer = AssetDepartmentHistorySerializer(asset_dept_history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DepartmentAssetPolicyAPI(APIView):
    def get(self, request, pk):
        asset_policies = AssetPolicy.objects.filter(department_id=pk)
        serializer = AssetPolicySerializer(asset_policies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountFixedAssetAPI(APIView):
    def get(self, reauest, pk):
        fixed_assets = FixedAssetRegister.objects.filter(account_id=pk)
        serializer =  FixedAssetRegisterSerializer(fixed_assets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AccountDepreciationAPI(APIView):
    def get(self, request,pk):
        depreciations = Depreciation.objects.filter(account_id=pk)
        serializer = DepreciationSerializer(depreciations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountGeneralLedgerAPI(APIView):
    def get(self, request, pk):
        general_ledgers = GeneralLedger.objects.filter(account_id=pk)
        serializer = GeneralLedgerSerializer(general_ledgers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)   

class AssetPolicyDisposalAPI(APIView):
    def get(self, request, pk):
        asset_disposals = AssetDisposal.objects.filter(policy_id=pk)
        serializer = AssetDisposalSerializer(asset_disposals, many=True)
        return Response (serializer.data, status = status.HTTP_200_OK)
    
class AssetPolicyDepreciationEventAPI(APIView):
    def get(self, request, pk):
        depreciation_events = DepreciationEvent.objects.filter(policy_id=pk)
        serializer = DepreciationEventSerializer(depreciation_events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DepreciationDepreEventAPI(APIView):
    def get(self, request, pk):
        depreciation_events = DepreciationEvent.objects.filter(depreciation_id=pk)
        serializer = DepreciationEventSerializer(depreciation_events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DepreciationAssetPolicyAPI(APIView):
    def get(self, request, pk):
        asset_policies = AssetPolicy.objects.filter(depreciation_id=pk)
        serializer = AssetPolicySerializer(asset_policies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FixedAssetDepreciationEventAPI(APIView):
    def get(self, request, pk):
        depreciation_events = DepreciationEvent.objects.filter(register_id=pk)
        serializer = DepreciationEventSerializer(depreciation_events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FixedAssetDepreciationAPI(APIView):
    def get(self, request, pk):
        depreciations = Depreciation.objects.filter(register_id=pk)
        serializer = DepreciationSerializer(depreciations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FixedAssetPolicyAPI(APIView):
    def get(self, request, pk):
        asset_policies = AssetPolicy.objects.filter(register_id=pk)
        serializer = AssetPolicySerializer(asset_policies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FixedAssetAdjustmentAPI(APIView):
    def get(self, request, pk):
        asset_adjustments = AssetAdjustment.objects.filter(register_id=pk)
        serializer = AssetAdjustmentSerializer(asset_adjustments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FixedAssetDeptHistoryAPI(APIView):
    def get(self, request, pk):
        asset_dept_histories = AssetDepartmentHistory.objects.filter(register_id=pk)
        serializer = AssetDepartmentHistorySerializer(asset_dept_histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FixedAssetDisposalAPI(APIView):
    def get(self, request, pk):
        asset_disposals = AssetDisposal.objects.filter(register_id=pk)
        serializer = AssetDisposalSerializer(asset_disposals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class FixedAssetComponentAPI(APIView):
    def get(self, request, pk):
        asset_components = AssetComponent.objects.filter(register_id=pk)
        serializer = AssetComponentSerializer(asset_components, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
