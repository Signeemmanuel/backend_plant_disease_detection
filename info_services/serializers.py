from rest_framework import serializers

class WeatherSerializer(serializers.Serializer):
    temperature = serializers.FloatField()
    humidity = serializers.IntegerField()
    description = serializers.CharField()
    icon = serializers.CharField()
    wind_speed = serializers.FloatField()
    pressure = serializers.IntegerField()

class NewsArticleSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    content = serializers.CharField()
    url = serializers.URLField()
    image_url = serializers.URLField(allow_blank=True)
    source = serializers.CharField()
    published_at = serializers.DateTimeField()

class NewsListSerializer(serializers.Serializer):
    articles = NewsArticleSerializer(many=True) 