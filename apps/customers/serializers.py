from rest_framework import serializers
from apps.customers.models import Customer
from decimal import Decimal

class CustomerSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    age = serializers.IntegerField(min_value=18, max_value=100)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if Customer.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return value
    
    def create(self, validated_data: dict) -> Customer:
        # Calculate approved limit: 36 * monthly_income, rounded to nearest lakh (100,000)
        monthly_income = validated_data['monthly_income']
        approved_limit = round(monthly_income * 36, -5)
        
        customer = Customer.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            age=validated_data['age'],
            monthly_income=monthly_income,
            phone_number=validated_data['phone_number'],
            approved_credit_limit=approved_limit,
        )
        return customer
    
class CustomerResponseSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'customer_id',
            'first_name',
            'last_name',
            'age',
            'phone_number',
            'monthly_income',
            'approved_credit_limit',
        ]