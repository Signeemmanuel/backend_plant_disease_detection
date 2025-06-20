from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, mixins, viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.dateparse import parse_datetime
from django.db.models import Q
import csv
from django.http import HttpResponse

from .serializers import MultiImageUploadSerializer, PredictionResponseSerializer, DetectionSerializer
from .models import Detection
from .utils.onnx_predictor import predict, is_preprocessed
from PIL import Image
import numpy as np

class PredictAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Predict plant disease from images",
        operation_description="Upload one or more images for plant disease prediction. Accepts `multipart/form-data` with an 'images' field.",
        request_body=MultiImageUploadSerializer,
        responses={200: PredictionResponseSerializer(many=True)},
    )
    def post(self, request):
        serializer = MultiImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        images = serializer.validated_data['images']

        results = []

        for img in images:
            try:
                img.seek(0)
                pred = predict(img)
            except Exception as e:
                return Response({"error": f"Prediction failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            if "error" in pred:
                return Response({"error": pred["error"]}, status=status.HTTP_400_BAD_REQUEST)

            detection = Detection.objects.create(
                user=request.user,
                image=img,
                result=pred["label"],
                confidence_score=pred["confidence"]
            )

            results.append({
                "filename": img.name,
                "predicted_class": pred["label"],
                "confidence_score": pred["confidence"],
            })

            img.seek(0)

        return Response(results, status=status.HTTP_200_OK)

class DetectionHistoryView(generics.ListAPIView):
    serializer_class = DetectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get prediction history",
        operation_description="Retrieve a paginated list of the user's past predictions.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Detection.objects.filter(user=self.request.user).order_by('-created_at')

class DetectionDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete a prediction",
        operation_description="Delete a specific prediction history item by its ID.",
    )
    def delete(self, request, pk):
        try:
            detection = Detection.objects.get(pk=pk, user=request.user)
        except Detection.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        detection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DetectionBulkDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Delete all predictions",
        operation_description="Delete all prediction history items for the authenticated user.",
    )
    def delete(self, request):
        deleted_count, _ = Detection.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FlagDetectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Flag a prediction",
        operation_description="Flag a prediction as incorrect. Admins can review flagged items.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'reason': openapi.Schema(type=openapi.TYPE_STRING, description='Reason for flagging.')}
        )
    )
    def post(self, request, pk):
        reason = request.data.get('reason', '')
        try:
            detection = Detection.objects.get(pk=pk, user=request.user)
        except Detection.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        detection.flagged = True
        detection.flag_reason = reason
        detection.save()
        return Response({'success': 'Flagged.'}, status=status.HTTP_200_OK)

class AdminFlaggedDetectionsView(generics.ListAPIView):
    serializer_class = DetectionSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="[Admin] List flagged predictions",
        operation_description="Retrieve all predictions that have been flagged by users for review.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Detection.objects.filter(flagged=True).order_by('-created_at')

class AdminStatsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="[Admin] Get system statistics",
        operation_description="Retrieve statistics like total users, predictions, and flagged items.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'prediction_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'flagged_count': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )}
    )
    def get(self, request):
        from django.contrib.auth.models import User
        user_count = User.objects.count()
        prediction_count = Detection.objects.count()
        flagged_count = Detection.objects.filter(flagged=True).count()
        return Response({
            'user_count': user_count,
            'prediction_count': prediction_count,
            'flagged_count': flagged_count
        })

class FilteredDetectionHistoryView(generics.ListAPIView):
    serializer_class = DetectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Filter prediction history",
        operation_description="Get a filtered list of predictions based on query parameters.",
        manual_parameters=[
            openapi.Parameter('result', openapi.IN_QUERY, description="Filter by disease name (partial match, case-insensitive)", type=openapi.TYPE_STRING),
            openapi.Parameter('min_conf', openapi.IN_QUERY, description="Minimum confidence score (e.g., 0.8)", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_conf', openapi.IN_QUERY, description="Maximum confidence score (e.g., 0.95)", type=openapi.TYPE_NUMBER),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Detection.objects.filter(user=self.request.user).order_by('-created_at')
        result = self.request.query_params.get('result')
        min_conf = self.request.query_params.get('min_conf')
        max_conf = self.request.query_params.get('max_conf')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if result:
            qs = qs.filter(result__icontains=result)
        if min_conf:
            qs = qs.filter(confidence_score__gte=float(min_conf))
        if max_conf:
            qs = qs.filter(confidence_score__lte=float(max_conf))
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        return qs

class ExportDetectionHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Export prediction history",
        operation_description="Download the user's complete prediction history as a CSV file.",
        responses={200: "CSV file of prediction history."}
    )
    def get(self, request):
        detections = Detection.objects.filter(user=request.user).order_by('-created_at')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="prediction_history.csv"'
        writer = csv.writer(response)
        writer.writerow(['id', 'result', 'confidence_score', 'created_at', 'latitude', 'longitude', 'flagged', 'flag_reason'])
        for d in detections:
            writer.writerow([d.id, d.result, d.confidence_score, d.created_at, d.latitude, d.longitude, d.flagged, d.flag_reason])
        return response
