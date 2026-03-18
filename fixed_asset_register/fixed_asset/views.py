from django.shortcuts import render
from datetime import datetime
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import status
from .models import *
from django.contrib.auth.hashers import check_password
from .serializers import *
from django.shortcuts import get_object_or_404
import traceback
from rest_framework.permissions import AllowAny
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth.models import User
import jwt
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
import requests as http_requests
from django.core.mail import send_mail
from .models import PasswordResetToken
from .serializers import ForgotPasswordSerializer
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
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

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


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
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user

    return Response({
        "name": user.name,
        "email": user.email,
        "role": user.role.role_name,  
        "department": user.department.dept_name
    })

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
            
            try:
                account = Account.objects.get(account_name=asset.fixed_asset_account)
            except Account.DoesNotExist:
                account = Account.objects.create(
                    account_name=asset.fixed_asset_account,
                    account_type='Asset'
                )
            
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
    

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            
            user = Users.objects.get(email=email)
            
            
            if check_password(password, user.password_hash):
                return Response({
                    "message": "Login Successful",
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "role": user.role.role_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
#  forgot password 
@api_view(['POST'])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return Response({"message": "If email exists, reset link sent"})

        token_obj = PasswordResetToken.objects.create(user=user)

       # reset_link = f"http://localhost:57300/#/reset-password?token={token_obj.token}"https://gentle-moss-03b9b8b0f.4.azurestaticapps.net
        reset_link = f"https://gentle-moss-03b9b8b0f.4.azurestaticapps.net/#/reset-password?token={token_obj.token}"

        send_mail(
            'Reset Your Password',
            f'Click this link: {reset_link}',
            settings.EMAIL_HOST_USER,
            [email],
        )

        return Response({"message": "Reset link sent to your email"})

    return Response(serializer.errors)

@api_view(['POST'])
def verify_token(request):
    token = request.data.get('token')

    try:
        token_obj = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return Response({"error": "Invalid token"}, status=400)

    if token_obj.is_expired():
        return Response({"error": "Token expired"}, status=400)

    return Response({"message": "Token valid"})

@api_view(['POST'])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)

    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            token_obj = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Invalid token"}, status=400)

        if token_obj.is_expired():
            return Response({"error": "Token expired"}, status=400)

        user = token_obj.user
        user.password_hash = make_password(new_password)
        user.save()

        token_obj.delete()

        return Response({"message": "Password reset successful"})

    return Response(serializer.errors)



User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    access_token = request.data.get("access_token")

    if not access_token:
        return Response({"error": "Access token missing"}, status=400)

    google_response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if google_response.status_code != 200:
        return Response({"error": "Invalid Google token"}, status=400)

    user_info = google_response.json()
    email = user_info.get("email")
    first_name = user_info.get("given_name", "")
    last_name = user_info.get("family_name", "")

    if not email:
        return Response({"error": "Email not provided by Google"}, status=400)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": email,
            "first_name": first_name,
            "last_name": last_name,
        }
    )

    refresh = RefreshToken.for_user(user)

  
    return Response({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "role": "user",  
            "department_name": "General", 
            "auth_provider": "google"
        },
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }, status=200)


@csrf_exempt
def azure_login_verify(request):
   
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        access_token = data.get('access_token')

        if not access_token:
            return JsonResponse({'error': 'Access token is required'}, status=400)

        
        graph_response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if graph_response.status_code == 200:
            ms_user = graph_response.json()
            user_email = ms_user.get('mail') or ms_user.get('userPrincipalName')
            user_name = ms_user.get('displayName')

          
            user, created = User.objects.get_or_create(
                email=user_email,
                defaults={
                    'username': user_email,
                    'first_name': user_name,
                    'auth_provider': 'microsoft',
                    'department_id': 1, 
                    'role_id': 1        
                }
            )

            return JsonResponse({
                'id': user.id,
                'email': user.email,
                'status': 'success'
            })
        else:
            return JsonResponse({'error': 'Invalid Microsoft Token'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    
class AssetBookViewSet(viewsets.ModelViewSet):
    queryset = AssetBook.objects.all()
    serializer_class = AssetBookSerializer

class SystemDefaultViewSet(viewsets.ModelViewSet):
    queryset = SystemDefault.objects.all()
    serializer_class = SystemDefaultSerializer

class ConventionListViewSet(viewsets.ModelViewSet):
    queryset = ConventionList.objects.all()
    serializer_class = ConventionListSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class BookLevelPolicyViewSet(viewsets.ModelViewSet):
    queryset = BookLevelPolicy.objects.all()
    serializer_class = BookLevelPolicySerializer

class AssetCategoryPolicyViewSet(viewsets.ModelViewSet):
    queryset = AssetCategoryPolicy.objects.all()
    serializer_class = AssetCategoryPolicySerializer



class LeaseContractViewSet(viewsets.ModelViewSet):
    queryset = LeaseContract.objects.all()
    serializer_class = LeaseContractSerializer
    
class LeaseFinancialViewSet(viewsets.ModelViewSet):
    present_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    queryset = LeaseFinancial.objects.all()
    serializer_class = LeaseFinancialSerializer

