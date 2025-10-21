from django.urls import path
from apps.loans.views import LoanDetailAPIView, CustomerLoansDetailAPIView, LoanEligibilityAPIView, LoanCreationView

urlpatterns = [
    path('view-loan/<int:loan_id>', LoanDetailAPIView.as_view(), name='loan-detail'),
    path('view-loans/<int:customer_id>', CustomerLoansDetailAPIView.as_view(), name='customer-loans'),
    path('check-eligibility', LoanEligibilityAPIView.as_view(), name='loan-eligibility'),
    path('create-loan', LoanCreationView.as_view(), name='loan-create'),
]
