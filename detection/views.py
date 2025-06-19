from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, mixins, viewsets
from drf_yasg.utils import swagger_auto_schema

from .serializers import MultiImageUploadSerializer, PredictionResponseSerializer, DetectionSerializer
from .models import Detection
from .utils.onnx_predictor import preprocess_image, predict, is_preprocessed
from PIL import Image
import numpy as np

class PredictAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Upload one or multiple images for plant disease prediction.",
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
                # Reset file pointer before reading
                img.seek(0)

                # Check if it's already preprocessed
                image = Image.open(img).convert("RGB")
                image_array = np.array(image)

                img.seek(0)  # Reset again for actual prediction

                if is_preprocessed(image_array):
                    pred = predict(img)  # Pass file-like object directly
                    preprocessed_on = "mobile"
                else:
                    pred = predict(img)
                    preprocessed_on = "backend"

            except Exception as e:
                # Fallback: try prediction anyway
                img.seek(0)
                pred = predict(img)
                preprocessed_on = "backend"

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
                "preprocessed_on": preprocessed_on
            })

            img.seek(0)  # Safe reset, though not needed further

        return Response(results, status=status.HTTP_200_OK)

class DetectionHistoryView(generics.ListAPIView):
    serializer_class = DetectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Detection.objects.filter(user=self.request.user)

class DetectionDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            detection = Detection.objects.get(pk=pk, user=request.user)
        except Detection.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        detection.delete()
        return Response({'success': 'Deleted.'}, status=status.HTTP_204_NO_CONTENT)

class DetectionBulkDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = Detection.objects.filter(user=request.user).delete()
        return Response({'success': f'Deleted {deleted_count} items.'}, status=status.HTTP_204_NO_CONTENT)
