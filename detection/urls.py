from django.urls import path
from .views import PredictAPIView, DetectionHistoryView, DetectionDeleteAPIView, DetectionBulkDeleteAPIView, FlagDetectionAPIView, AdminFlaggedDetectionsView, AdminStatsAPIView, FilteredDetectionHistoryView, ExportDetectionHistoryAPIView

urlpatterns = [
    path('', PredictAPIView.as_view(), name='predict'),
    path('history/', DetectionHistoryView.as_view(), name='detection_history'),
    path('history/<int:pk>/', DetectionDeleteAPIView.as_view(), name='detection_history_delete'),
    path('history/delete_all/', DetectionBulkDeleteAPIView.as_view(), name='detection_history_delete_all'),
    path('history/filtered/', FilteredDetectionHistoryView.as_view(), name='filtered_detection_history'),
    path('history/export/', ExportDetectionHistoryAPIView.as_view(), name='export_detection_history'),
    path('history/<int:pk>/flag/', FlagDetectionAPIView.as_view(), name='flag_detection'),
    path('admin/flagged/', AdminFlaggedDetectionsView.as_view(), name='admin_flagged_detections'),
    path('admin/stats/', AdminStatsAPIView.as_view(), name='admin_stats'),
]