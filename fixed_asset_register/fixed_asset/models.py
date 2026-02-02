from django.db import models
from django.core.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal


class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    company_code = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    branch = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'company'

    def __str__(self):
        return self.company_name
    

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column='company_id')
    dept_code = models.CharField(max_length=255)
    dept_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'department'

    def __str__(self):
        return self.dept_name




class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    account_code = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=100)
    currency = models.CharField(max_length=3)

    class Meta:
        db_table = 'account'

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class GeneralLedger(models.Model):
    SOURCE_TYPES = [
        ('WIP', 'WIP'),
        ('FA', 'Fixed Asset'),
        ('EXPENSE', 'Expense'),
    ]

    REF_TYPES = [
        ('Expense', 'Expense'),
        ('Depreciation', 'Depreciation'),
    ]

    gl_id = models.AutoField(primary_key=True)
    source_id = models.IntegerField(null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    gl_code = models.IntegerField()
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    ref_type = models.CharField(max_length=20, choices=REF_TYPES)
    account_code = models.CharField(max_length=255)
    gl_date = models.DateField()
    description = models.CharField(max_length=500, blank=True, null=True)
    debit_amount = models.FloatField(default=0)
    credit_amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'general_ledger'

   

class GLAllocation(models.Model):
    ALLOCATION_TYPES = [
        ('WIP', 'WIP'),
        ('FA', 'Fixed Asset'),
        ('EXPENSE', 'Expense'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    gl_allocation_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    gl = models.ForeignKey(GeneralLedger, on_delete=models.CASCADE)
    allocation_type = models.CharField(max_length=20, choices=ALLOCATION_TYPES)
    allocation_amount = models.FloatField()
    account_code = models.CharField(max_length=255)
    reason = models.CharField(max_length=500, blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gl_allocation'
    
    def __str__(self):
        return f"GL Allocation {self.gl_allocation_id}"


class WorkInProgress(models.Model):
    STATUS_CHOICES = [
        ('progress', 'Progress'),
        ('completed', 'Completed'),
        ('capitalized', 'Capitalized'),
    ]

    wip_id = models.AutoField(primary_key=True)
    gl_allocation = models.ForeignKey(GLAllocation, on_delete=models.SET_NULL, null=True, blank=True)
    wip_code = models.CharField(max_length=255)
    project_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    total_amount = models.FloatField()
    currency = models.CharField(max_length=3)

    class Meta:
        db_table = 'work_in_progress'

    def __str__(self):
        return self.wip_code


class WIPItem(models.Model):
    COST_TYPES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ]

    wip_item_id = models.AutoField(primary_key=True)
    wip = models.ForeignKey(WorkInProgress, on_delete=models.CASCADE)
    item_code = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255)
    cost_type = models.CharField(max_length=20, choices=COST_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.FloatField()
    unit_cost = models.FloatField()
    total_cost = models.FloatField()
    currency = models.CharField(max_length=3)
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wip_item'

    def __str__(self):
        return self.item_name
    
    def save(self, *args, **kwargs):
        if self.quantity is not None and self.unit_cost is not None :
            self.total_cost = self.quantity * self.unit_cost

        super().save(*args, **kwargs)


class FixedAssetRegister(models.Model):
    ASSET_STATUS = [
        ('Finished', 'Finished'),
        ('Ready to Use', 'Ready to Use'),
        ('No Depreciation', 'No Depreciation'),
        ('Disposal', 'Disposal'),
    ]

    CURRENCY_TYPE = [
        ('MMK', 'MMK'),
        ('USD', 'USD'),
        ('CNY', 'CNY'),
        ('THB', 'THB'),
        ('JPY', 'JPY'),
        ('SGD', 'SGD'),
    ]

    SOURCE_TYPE = [
        ('WIP', 'WIP'),
        ('DIRECT', 'Direct'),
    ]

    ASSET_TYPE = [
        ('MAIN', 'MAIN'),
        ('COMPONENT', 'COMPONENT'),
        
    ]

    PERIOD = [
        ('DAY', 'DAY'),
        ('MONTH', 'MONTH'),
        ('YEAR', 'YEAR'),
    ]
    
    COMPUTATION = [
        ('DAY', 'DAY'),
        ('MONTH', 'MONTH'),
        ('YEAR', 'YEAR'),
    ]

    Depreciation_METHOD = [
        ('Straight Line', 'Straight Line'),
        ('Reducing Balance', 'Reducing Balance'),
        ('Double Declining', 'Double Declining'),
    ]

    register_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    wip = models.ForeignKey(WorkInProgress, on_delete=models.SET_NULL, null=True, blank=True)
    gl_allocation = models.ForeignKey(GLAllocation, on_delete=models.SET_NULL, null=True, blank=True)
    fixed_asset_code = models.CharField(max_length=255)
    fixed_asset_account = models.CharField(max_length=255)
    acquisition_date = models.DateField()
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE)
    asset_status = models.CharField(max_length=30, choices=ASSET_STATUS)
    asset_name = models.CharField(max_length=255)
    asset_model = models.CharField(max_length=255, blank=True, null=True)
    asset_group = models.CharField(max_length=255, blank=True, null=True)
    asset_type = models.CharField(max_length=30, choices=ASSET_TYPE)
    description = models.CharField(max_length=500, blank=True, null=True)
    useful_life = models.IntegerField()
    period = models.CharField(max_length=30, choices=PERIOD)
    capitalization_date = models.DateTimeField(null=False, blank=False)
    home_currency = models.CharField(max_length=3, default='MMK')
    transaction_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE)
    exchange_rate = models.FloatField()
    acquisition_cost = models.FloatField()
    home_acquisition_cost = models.FloatField()
    residual_value = models.FloatField()
    residual_currency = models.CharField(max_length=3,  choices=CURRENCY_TYPE)
    transportation_fee = models.FloatField()
    transportation_currency = models.CharField(max_length=3,  choices=CURRENCY_TYPE)
    tax = models.FloatField()
    tax_fee_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE)
    other_fee = models.FloatField()
    other_fee_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE)
    total_amount = models.FloatField()
    total_amount_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE)
    computation = models.CharField(max_length=30, choices=COMPUTATION)
    addition_amount = models.FloatField()
    additional_amount_currency = models.CharField(max_length=3, choices=CURRENCY_TYPE)
    depreciation_method = models.CharField(max_length=30, choices=Depreciation_METHOD)
    current_nbv = models.FloatField()
    depreciation_account = models.CharField(max_length=255)
    expense_account = models.CharField(max_length=255)
    supplier = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'fixed_asset_register'

    def __str__(self):
        return self.fixed_asset_code
    
    def clean(self):
        if self.asset_status in ['Finished', 'Ready to use']and self.addition_amount > 0:
                raise ValidationError({
                    'addition_amount':'Addition amount is not allowed when asset status is Finished or Ready to Use.'
                })


    def get_total_depreciation_units(self):
        if self.useful_life <= 0 :
            return 0
        
        if self.period == self.computation:
            return self.useful_life
        
        if self.period == 'YEAR':
            total_days = self.useful_life *365

        elif self.period == 'MONTH':
            total_days = self.useful_life * 30

        else:
            total_days = self.useful_life

        if self.computation == 'YEAR':
            return total_days // 365
        
        elif self.computation == 'MONTH':
            return total_days // 30
        else:
            return total_days
        
    def get_elasped_units(self):
        if not self.capitalization_date:
            return 0
        today = date.today()
        start_date = self.capitalization_date

        if isinstance(start_date, datetime):
            start_date = start_date.date()

        if today <= start_date:
            return 0

        delta = relativedelta(today, start_date)

        if self.computation == 'YEAR':
            return delta.years
        
        elif self.computation == 'MONTH':
            return delta.years * 12 + delta.months

        else:
            return (today - start_date).days
        
        
    
    def straight_line_accumulated(self):
        total_units = self.get_total_depreciation_units()
        if total_units == 0 :
            return 0
        elasped_units = min(self.get_elasped_units(), total_units)

        depreciation_amount = self.total_amount - self.residual_value
        depreciation_per_unit = depreciation_amount / total_units

        return round(depreciation_per_unit * elasped_units, 2)
    
    
    def reducing_balance_accumulated(self):
        total_units = self.get_total_depreciation_units()
        if total_units == 0:
            return 0.0

        elapsed_units = min(self.get_elasped_units(), total_units)

        cost = Decimal(str(self.total_amount))
        residual = Decimal(str(self.residual_value))

        
        annual_rate = Decimal("1") / Decimal(str(self.useful_life))
        computation = self.computation.upper()
        if computation == "YEAR":
            period_rate = annual_rate
        elif computation == "MONTH":
            period_rate = annual_rate / Decimal("12")
        elif computation == "DAY":
            period_rate = annual_rate / Decimal("365")
        else:
            period_rate = annual_rate
        nbv = cost

        for _ in range(int(elapsed_units)):
            depreciation = nbv * period_rate
            nbv -= depreciation

            if nbv <= residual:
                nbv = residual
                break

        accumulated = cost - nbv
        return float(accumulated.quantize(Decimal("0.01")))
    
    def double_declining_accumulated(self):
        total_units = self.get_total_depreciation_units()
        if total_units == 0:
            return 0.0

        elapsed_units = min(self.get_elasped_units(), total_units)

        cost = Decimal(str(self.total_amount))
        residual = Decimal(str(self.residual_value))

        annual_rate = Decimal("2") / Decimal(str(self.useful_life))
        computation = self.computation.upper()
        if computation == "YEAR":
            period_rate = annual_rate
        elif computation == "MONTH":
            period_rate = annual_rate / Decimal("12")
        elif computation == "DAY":
            period_rate = annual_rate / Decimal("365")
        else:
            period_rate = annual_rate
        nbv = cost

        for _ in range(int(elapsed_units)):
            depreciation = nbv * period_rate
            nbv -= depreciation

            if nbv <= residual:
                nbv = residual
                break

        accumulated = cost - nbv
        return float(accumulated.quantize(Decimal("0.01")))

    def calculate_current_nbv(self):
        if self.asset_status == 'No Depreciation':
            return round(self.total_amount, 2)
        
        if self.total_amount <= self.residual_value:
            return round(self.residual_value, 2)
        
        if self.depreciation_method == 'Straight Line':
            accumulated = self.straight_line_accumulated()

        elif self.depreciation_method == 'Double Declining':
            accumulated = self.double_declining_accumulated()

        else:
            accumulated = self.reducing_balance_accumulated()

        nbv = self.total_amount - accumulated
        return round(max(nbv, self.residual_value), 2)
    
    def save(self, *args, **kwargs):
        # self.full_clean()

        if self.exchange_rate is not None and self.acquisition_cost is not None:
            self.home_acquisition_cost = self.exchange_rate * self. acquisition_cost

        self.total_amount = (
            (self.transportation_fee or 0) +
            (self.other_fee or 0) +
            (self.tax or 0) +
            (self.home_acquisition_cost or 0)
        )
        
        if self.depreciation_method == 'Reducing Balance':
            self.current_nbv = self.calculate_current_nbv()
        elif self.depreciation_method == 'Double Declining':
            self.current_nbv = self.calculate_current_nbv()
        elif self.depreciation_method == 'Straight Line':
            self.current_nbv = self.calculate_current_nbv() 
        super().save(*args, **kwargs)




class AssetComponent(models.Model):

    PERIOD_CHOICES = [
        ('Day', 'Day'),
        ('Month', 'Month'),
        ('Year', 'Year'),
    ]

    component_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(
        'FixedAssetRegister',
        on_delete=models.CASCADE,
        related_name='asset_components'
    )

    component_type = models.CharField(max_length=100)

    install_date = models.DateTimeField(null=True, blank=True)
    uninstall_date = models.DateTimeField(null=True, blank=True)
    capitalization_date = models.DateTimeField(null=True, blank=True)

    remark = models.CharField(max_length=255, null=True, blank=True)

    cost = models.FloatField(default=0)
    currency = models.CharField(max_length=3, default='MMK')

    useful_life = models.IntegerField(
        help_text="Useful life value based on selected period"
    )

    period = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        db_table = 'asset_component'
        ordering = ['component_id']

    def __str__(self):
        return f"{self.component_type} (Asset ID: {self.register_id})"


class Depreciation(models.Model):
    depreciation_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(FixedAssetRegister, on_delete=models.CASCADE, db_column='register_id')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='account_id')
    depreciation_date = models.DateField()
    method = models.CharField(max_length=100)
    computation = models.CharField(max_length=100)
    book_value = models.FloatField()
    journal = models.CharField(max_length=255)
    depreciation_rate = models.FloatField()

    class Meta:
        db_table = 'depreciation'

    def __str__(self):
        return f"Depreciation {self.depreciation_id}"



class AssetPolicy(models.Model):
    PERIOD = [
        ('DAY', 'DAY'),
        ('MONTH', 'MONTH'),
        ('YEAR', 'YEAR'),
    ]
    METHOD_CHOICES = [
        ('Straight Line', 'Straight Line'),
        ('Reducing Balance', 'Reducing Balance'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    policy_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(FixedAssetRegister, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    depreciation = models.ForeignKey(Depreciation, on_delete=models.CASCADE)
    useful_life = models.IntegerField()
    period = models.CharField(max_length=5, choices=PERIOD)
    status = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES
    )

    amount = models.FloatField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    remark = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'asset_policy'

    def __str__(self):
        return f"Policy {self.policy_id}"


class DepreciationEvent(models.Model):
    event_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(FixedAssetRegister, on_delete=models.CASCADE, db_column='register_id')
    policy = models.ForeignKey(AssetPolicy, on_delete=models.CASCADE, db_column='policy_id')
    depreciation = models.ForeignKey(Depreciation, on_delete=models.CASCADE, db_column='depreciation_id')
    depreciation_date = models.DateField()
    depreciation_amount = models.FloatField()
    accumulated_depreciation = models.FloatField()
    nbv_depreciation = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'depreciation_event'

    def __str__(self):
        return f"Depreciation Event {self.event_id}"




class AssetDisposal(models.Model):
    DISPOSAL_TYPE_CHOICES = [
        ('Sale', 'Sale'),
        ('Scrap', 'Scrap'),
        ('WriteOff', 'Write Off'),
    ]

    COMPUTATION_CHOICES = [
        ('Gain', 'Gain'),
        ('Loss', 'Loss'),
    ]
    asset_disposal_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(FixedAssetRegister, on_delete=models.CASCADE,  db_column='register_id')
    policy = models.ForeignKey(
        'AssetPolicy',
        on_delete=models.CASCADE,
        db_column='policy_id'
    )
    disposal_date = models.DateField()
    disposal_type = models.CharField(
        max_length=20,
        choices=DISPOSAL_TYPE_CHOICES
    )
    computation = models.CharField(
        max_length=10,
        choices=COMPUTATION_CHOICES
    )
    proceeds_amount = models.FloatField()
    book_value = models.FloatField()
    gain_loss = models.FloatField()
    remark = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'asset_disposal'

    def __str__(self):
        return f"Disposal {self.asset_disposal_id}"
    
    def save(self, *args, **kwargs):
        if self.proceeds_amount is not None and self.book_value is not None:
            self.gain_loss = self.proceeds_amount - self.book_value

        super().save(*args, **kwargs)


class AssetAdjustment(models.Model):
    ADJUSTMENT_TYPE_CHOICES = [
        ('Additional Cost', 'Additional Cost'),
        ('Changing Useful life', 'Changing Useful Life'),
        ('Changing Depreciation Method', 'Changing Depreciation Method'),
        ('Disposal', 'Disposal'),
        ('Write Off', 'Write Off'),
        ('Impairment', 'Impairment'),
        ('Transfer Location', 'Transfer Location'),
        ('Partial Disposal', 'Partial Disposal'),
        ('Component Repalcement', 'Component Replacement'),
        ('Residual Value Change', 'Residual Value Change'),
        ('Revaluation', 'Revaluation'),
        ('Overhaul Cost', 'Overhaul Cost'),
    ]
    asset_adjustment_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(FixedAssetRegister, on_delete=models.CASCADE, db_column='register_id')
    adjustment_date = models.DateTimeField()
    adjustment_type = models.CharField(
        max_length=50,
        choices=ADJUSTMENT_TYPE_CHOICES
    )

    old_value = models.FloatField()
    new_value = models.FloatField()
    remark = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'asset_adjustment'

    def __str__(self):
        return f"Adjustment {self.asset_adjustment_id}"


class AssetDepartmentHistory(models.Model):
    dept_history_id = models.AutoField(primary_key=True)
    register = models.ForeignKey(FixedAssetRegister, on_delete=models.CASCADE,  db_column='register_id')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_column='dept_id')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    remark = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'asset_dept_history'

    def __str__(self):
        return f"Dept History {self.dept_history_id}"
    


