from django.urls import path
from .views import PredictAPIView, DetectionHistoryView, DetectionDeleteAPIView, DetectionBulkDeleteAPIView

urlpatterns = [
    path('', PredictAPIView.as_view(), name='predict'),
    path('history/', DetectionHistoryView.as_view(), name='detection_history'),
    path('history/<int:pk>/', DetectionDeleteAPIView.as_view(), name='detection_history_delete'),
    path('history/delete_all/', DetectionBulkDeleteAPIView.as_view(), name='detection_history_delete_all'),
]