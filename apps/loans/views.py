from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.services import LoanEligibilityService, LoanCreationService
from apps.loans.serializers import LoanDetailSerializer, LoanEligibilityRequestSerializer, LoanEligibilityResponseSerializer, LoanCreationResponseSerializer
from apps.loans.models import Loan
from apps.customers.models import Customer

class LoanDetailAPIView(APIView):
    def get(self, request, loan_id, *args, **kwargs):
        try:
            loan = Loan.objects.get(pk=loan_id)
        except Loan.DoesNotExist:
            return Response({"detail": "Loan not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CustomerLoansDetailAPIView(APIView):
    def get(self, request, customer_id, *args, **kwargs):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        loans = Loan.objects.filter(customer_id=customer)
        serializer = LoanDetailSerializer(loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LoanEligibilityAPIView(APIView):
    def post(self, request) -> Response:
        request_serializer = LoanEligibilityRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = request_serializer.validated_data

        eligibility_result = LoanEligibilityService.check_eligibility(
            customer_id=validated_data['customer_id'],
            loan_amount=validated_data['loan_amount'],
            interest_rate=validated_data['interest_rate'],
            tenure_months=validated_data['term_months']
        )
        response_data: dict = {
            'customer_id': validated_data['customer_id'],
            'approval': eligibility_result['approval'],
            'interest_rate': eligibility_result['interest_rate'],
            'corrected_interest_rate': eligibility_result['corrected_interest_rate'],
            'term_months': validated_data['term_months'],
            'monthly_payment': eligibility_result['monthly_payment'],
            'reason': eligibility_result.get('message', 'Loan approved.')
        }

        response_serializer = LoanEligibilityResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
    
class LoanCreationView(APIView):
    def post(self, request):
        request_serializer = LoanEligibilityRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = request_serializer.validated_data

        creation_response = LoanCreationService.create_loan(
            customer_id=validated_data['customer_id'],
            loan_amount=validated_data['loan_amount'],
            interest_rate=validated_data['interest_rate'],
            term_months=validated_data['term_months']
        )
        
        response_serializer = LoanCreationResponseSerializer(data=creation_response)
        response_serializer.is_valid(raise_exception=True)

        if creation_response['loan_approved']:
            return Response(response_serializer.validated_data, status=status.HTTP_201_CREATED)
        else:
            return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
