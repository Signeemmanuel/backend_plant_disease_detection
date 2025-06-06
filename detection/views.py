from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema

from .serializers import MultiImageUploadSerializer, PredictionResponseSerializer
from .utils.onnx_predictor import preprocess_image, predict, is_preprocessed
from PIL import Image
import numpy as np

class PredictAPIView(APIView):
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated

    @swagger_auto_schema(
        operation_description="Upload one or multiple images for plant disease prediction.",
        request_body=MultiImageUploadSerializer,
        responses={200: PredictionResponseSerializer(many=True)},
    )
    # def post(self, request):
    #     serializer = MultiImageUploadSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     images = serializer.validated_data['images']

    #     results = []

    #     for img in images:
    #         img_bytes = img.read()
    #         try:
    #             # Try loading image as numpy array to check preprocessing
    #             image = Image.open(img)
    #             image_array = np.array(image)

    #             if is_preprocessed(image_array):
    #                 # Already preprocessed on mobile, just run predict directly
    #                 pred = predict(img_bytes)  
    #                 preprocessed_on = "mobile"
    #             else:
    #                 # Not preprocessed, do preprocessing and prediction
    #                 pred = predict(img_bytes)
    #                 preprocessed_on = "backend"
    #         except Exception as e:
    #             # Fallback to backend preprocessing and prediction if any error occurs
    #             pred = predict(img_bytes)
    #             preprocessed_on = "backend"

    #         if "error" in pred:
    #             return Response({"error": pred["error"]}, status=status.HTTP_400_BAD_REQUEST)

    #         results.append({
    #             "filename": img.name,
    #             "predicted_class": pred["label"],
    #             "confidence_score": pred["confidence"],
    #             "preprocessed_on": preprocessed_on
    #         })

    #         # Reset file pointer for next use (important!)
    #         img.seek(0)

    #     return Response(results, status=status.HTTP_200_OK)
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

            results.append({
                "filename": img.name,
                "predicted_class": pred["label"],
                "confidence_score": pred["confidence"],
                "preprocessed_on": preprocessed_on
            })

            img.seek(0)  # Safe reset, though not needed further

        return Response(results, status=status.HTTP_200_OK)
