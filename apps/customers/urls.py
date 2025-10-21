from django.urls import path
from apps.customers.views import CustomerAPIView

urlpatterns = [
    path('register', CustomerAPIView.as_view(), name='customer-register'),
]