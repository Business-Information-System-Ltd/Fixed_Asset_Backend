from rest_framework import serializers
from .models import *

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class GeneralLedgerSerializer(serializers.ModelSerializer):
    account_code = serializers.ReadOnlyField(source='account.account_code')
    source_id = serializers.ReadOnlyField()
    source_type = serializers.ChoiceField(choices=GeneralLedger.SOURCE_TYPES)


    wip = serializers.PrimaryKeyRelatedField(
        queryset=WorkInProgress.objects.all(),
        required=False,
        write_only=True
    )
    register = serializers.PrimaryKeyRelatedField(
        queryset=FixedAssetRegister.objects.all(),
        required=False,
        write_only=True
    )

    class Meta:
        model = GeneralLedger
        fields = '__all__'

    def validate(self, data):
        source_type = data.get('source_type')
        wip = data.get('wip')
        register = data.get('register')

        if source_type == 'WIP':
            if not wip:
                raise serializers.ValidationError({"wip": "WIP must be provided when source_type is WIP."})
            data['register'] = None 

        elif source_type == 'FA':
            if not register:
                raise serializers.ValidationError({"register": "Register must be provided when source_type is FA."})
            data['wip'] = None  

        elif source_type == 'EXPENSE':
            data['wip'] = None
            data['register'] = None

        else:
            raise serializers.ValidationError({"source_type": "Invalid source_type."})

        return data

    def create(self, validated_data):
        wip = validated_data.pop('wip', None)
        register = validated_data.pop('register', None)
        source_type = validated_data.get('source_type')

        
        if source_type == 'WIP' and wip:
            validated_data['source_id'] = wip.wip_id
        elif source_type == 'FA' and register:
            validated_data['source_id'] = register.register_id
        else:
            validated_data['source_id'] = None

        
        account = validated_data.get('account')
        if account:
            validated_data['account_code'] = account.account_code

        return super().create(validated_data)

    def update(self, instance, validated_data):
        wip = validated_data.pop('wip', None)
        register = validated_data.pop('register', None)
        source_type = validated_data.get('source_type', instance.source_type)

       
        if source_type == 'WIP' and wip is not None:
            instance.source_id = wip.wip_id
            instance.register = None
        elif source_type == 'FA' and register is not None:
            instance.source_id = register.register_id
            instance.wip = None
        elif source_type == 'EXPENSE':
            instance.source_id = None
            instance.wip = None
            instance.register = None

        
        account = validated_data.get('account', instance.account)
        if account:
            instance.account_code = account.account_code

        return super().update(instance, validated_data)


class GLAllocationSerializer(serializers.ModelSerializer):
    account_code = serializers.ReadOnlyField(source='account.account_code')
    class Meta:
        model = GLAllocation
        fields = '__all__'

    def create(self, validated_data):
        account = validated_data.get('account')
        if account:
            validated_data['account_code'] = account.account_code

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        account = validated_data.get('account', instance.account)
        if account:
            instance.account_code = account.account_code
        return super().update(instance, validated_data)


class WorkInProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkInProgress
        fields = '__all__'

class WIPItemSerializer(serializers.ModelSerializer):
    total_cost = serializers.FloatField(read_only=True)
    class Meta:
        model = WIPItem
        fields = '__all__'

class FixedAssetRegisterSerializer(serializers.ModelSerializer):
    asset_group = serializers.ReadOnlyField(source='account.account_name')
    home_acquisition_cost = serializers.FloatField(read_only=True)
    total_amount = serializers.FloatField(read_only= True)
    current_nbv = serializers.FloatField(read_only=True)
    class Meta:
        model = FixedAssetRegister
        fields = '__all__'

    def create(self, validated_data):
        account=validated_data.get('account')
        if account:
            validated_data['asset_group'] = account.account_name
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        account=validated_data.get('account', instance.account)
        if account:
            instance.asset_group = account.account_name
        return super().update(instance, validated_data)
    
class AssetComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetComponent
        fields = '__all__'


class DepreciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depreciation
        fields = '__all__'

class AssetPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetPolicy
        fields = '__all__'

class DepreciationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepreciationEvent
        fields = '__all__'

class AssetDisposalSerializer(serializers.ModelSerializer):
    gain_loss = serializers.FloatField(read_only=True)
    class Meta:
        model = AssetDisposal
        fields = '__all__'

class AssetAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetAdjustment
        fields = '__all__'

class AssetDepartmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetDepartmentHistory
        fields = '__all__'

class FixedAssetFullSerializer (serializers.ModelSerializer):
    asset_components = AssetComponentSerializer(many=True, read_only=True)
    depreciations = DepreciationSerializer(
        source='depreciation_set', many=True, read_only=True
    )
    depreciation_events = DepreciationEventSerializer(
        source='depreciation_event_set', many=True, read_only=True
    )
    asset_policies = AssetPolicySerializer(
        source='assetpolicy_set', many = True, read_only=True
    )
    asset_disposals = AssetDisposalSerializer(
        source='assetdisposal_set', many=True, read_only=True
    )
    asset_adjustments = AssetAdjustmentSerializer(
        source='assetadjustment_set', many=True, read_only=True
    )
    asset_dept_histories = AssetDepartmentHistorySerializer(
        source='assetdepartmenthistory_set', many=True, read_only=True
    )

    class Meta:
        model = FixedAssetRegister
        fields = '__all__'