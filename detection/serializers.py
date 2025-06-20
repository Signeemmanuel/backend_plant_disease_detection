from rest_framework import serializers
from .models import Detection

class MultiImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        allow_empty=False,
        help_text="Upload one or more images for prediction."
    )

class PredictionResponseSerializer(serializers.Serializer):
    filename = serializers.CharField()
    predicted_class = serializers.CharField()
    confidence_score = serializers.FloatField()
    preprocessed_on = serializers.CharField()  # 'mobile' or 'backend'

class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = ('id', 'user', 'image', 'result', 'confidence_score', 'created_at', 'flagged', 'flag_reason')
        read_only_fields = ('user',)
