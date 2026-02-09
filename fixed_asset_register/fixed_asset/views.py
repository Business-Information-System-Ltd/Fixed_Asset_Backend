from django.shortcuts import render
from datetime import datetime
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404
import traceback
from rest_framework.permissions import AllowAny
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


class ExecuteDepreciationAPI(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            data = request.data
            asset_id = data.get('fixed_asset_id')
            calculation_result = data.get('calculation_result', {})
            show_in_journal = data.get('show_in_journal', False)
            
            if not asset_id:
                return Response({'error': 'Asset ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            asset = FixedAssetRegister.objects.get(pk=asset_id)
            
            
            if asset.asset_status.lower() != 'ready to use':
                return Response({
                    'error': f'Asset status must be "Ready to Use". Current status: {asset.asset_status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create account
            try:
                account = Account.objects.get(account_name=asset.fixed_asset_account)
            except Account.DoesNotExist:
                account = Account.objects.create(
                    account_name=asset.fixed_asset_account,
                    account_type='Asset'
                )
            
            # Create Depreciation record
            depreciation = Depreciation.objects.create(
                register=asset,
                account=account,
                depreciation_date=timezone.now().date(),
                method=asset.depreciation_method,
                computation=asset.computation,
                book_value=calculation_result.get('current_nbv', asset.current_nbv),
                journal='Depreciation Journal Entry' if show_in_journal else '',
                depreciation_rate=0.0,  
            )
            
            #  Get or create AssetPolicy
            policy, created = AssetPolicy.objects.get_or_create(
                register=asset,
                defaults={
                    'useful_life': asset.useful_life,
                    'period': asset.period,
                    'start_date': asset.capitalization_date,
                    'end_date': asset.capitalization_date + timedelta(days=asset.useful_life * 365),
                    'method': asset.depreciation_method,
                    'amount': calculation_result.get('depreciation_amount', 0),
                    'status': 'Active',
                    'remark': f'Auto-generated policy for {asset.fixed_asset_code}',
                }
            )
            
            #  Create DepreciationEvent
            depreciation_event = DepreciationEvent.objects.create(
                register=asset,
                policy=policy,
                depreciation=depreciation,
                depreciation_date=timezone.now().date(),
                depreciation_amount=calculation_result.get('depreciation_amount', 0),
                accumulated_depreciation=calculation_result.get('accumulated_depreciation', 0),
                nbv_depreciation=calculation_result.get('current_nbv', asset.current_nbv),
            )
            
          
            asset.current_nbv = calculation_result.get('current_nbv', asset.current_nbv)
            
            # Check if asset is fully depreciated
            if asset.current_nbv <= asset.residual_value:
                asset.asset_status = 'Finished'
            
            asset.save()
            
            return Response({
                'success': True,
                'message': 'Depreciation executed successfully',
                'depreciation_id': depreciation.depreciation_id,
                'event_id': depreciation_event.event_id,
                'policy_id': policy.policy_id,
                'new_nbv': asset.current_nbv,
            }, status=status.HTTP_201_CREATED)
            
        except FixedAssetRegister.DoesNotExist:
            return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e), 'traceback': traceback.format_exc()}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class SignupView(APIView):
    def get(self, request):
        users = Users.objects.all() 
        serializer = UserSignupSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)