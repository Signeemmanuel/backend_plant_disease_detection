from django.urls import path
from .views import PredictAPIView

urlpatterns = [
    path('', PredictAPIView.as_view(), name='predict'),
]