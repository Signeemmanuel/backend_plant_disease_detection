import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import WeatherSerializer, NewsListSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime

# Create your views here.

class WeatherAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Get current weather",
        operation_description="Get current weather for a given latitude and longitude using OpenWeatherMap.",
        manual_parameters=[
            openapi.Parameter('latitude', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True, description='Latitude'),
            openapi.Parameter('longitude', openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True, description='Longitude'),
        ],
        responses={200: WeatherSerializer()}
    )
    def get(self, request):
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        if not lat or not lon:
            return Response({'error': 'latitude and longitude are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return Response({'error': 'Invalid latitude or longitude.'}, status=status.HTTP_400_BAD_REQUEST)
        api_key = getattr(settings, 'OPENWEATHERMAP_API_KEY', '')
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            weather = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'pressure': data['main']['pressure'],
            }
            return Response(weather)
        except Exception as e:
            return Response({'error': f'Weather service unavailable: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)

class NewsAPIView(APIView):
    @swagger_auto_schema(
        operation_summary="Get latest agricultural news",
        operation_description="Get recent agricultural news articles, cached for 24 hours. The cache is refreshed automatically after 24 hours or on the first request after expiration.",
        responses={200: NewsListSerializer()}
    )
    def get(self, request):
        cache_key = 'agri_news_cache'

        # Attempt to retrieve data from cache
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response({'articles': cached_data})

        api_key = getattr(settings, 'NEWSAPI_API_KEY', '')
        if not api_key:
            return Response(
                {'error': 'News API key is not configured in settings.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # url = f'https://newsapi.org/v2/everything?q=agriculture&language=en&sortBy=publishedAt&pageSize=10&apiKey={api_key}'
        
        # Define relevant domains (you'll need to research and test these)
        # Make sure these are domains covered by NewsAPI's 'everything' endpoint
        agricultural_domains = "agriculture.com,farmprogress.com,agweb.com,thepacker.com,capitalpress.com" # Add more as needed

        # Combine general agriculture query with domain filtering for better relevance
        # Note: NewsAPI recommends 'q' AND 'domains' for best results, rather than just 'domains' alone.
        # Also, NewsAPI requires 20% of 'domains' traffic to be from the paid tier if you use more than 5.
        # For free tier, keep the domains count low.
        url = (
            f'https://newsapi.org/v2/everything?'
            f'q=agriculture%20OR%20farming%20OR%20crops%20OR%20livestock%20OR%20agribusiness&'
            # f'domains={agricultural_domains}&'
            f'language=en&'
            f'sortBy=publishedAt&'
            f'pageSize=10&'
            f'apiKey={api_key}'
        )
        

        try:
            resp = requests.get(url, timeout=10) # Set a timeout for the request
            resp.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

            data = resp.json()
            articles = []
            for a in data.get('articles', []):
                articles.append({
                    'title': a.get('title', ''),
                    'description': a.get('description', ''),
                    'content': a.get('content', ''),
                    'url': a.get('url', ''),
                    'image_url': a.get('urlToImage', ''),
                    'source': a.get('source', {}).get('name', ''),
                    # Use a default if 'publishedAt' is missing, though it's usually present
                    'published_at': a.get('publishedAt', datetime.utcnow().isoformat()),
                })

            # Cache the fetched articles for 24 hours (86400 seconds)
            # 24 hours * 60 minutes/hour * 60 seconds/minute = 86400 seconds
            cache.set(cache_key, articles, 24 * 60 * 60) # Set cache expiration to 24 hours

            return Response({'articles': articles})

        except requests.exceptions.RequestException as e:
            # Catch specific requests exceptions (e.g., network issues, timeouts, invalid URL)
            return Response(
                {'error': f'News service communication error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except ValueError as e:
            # Catch JSON decoding errors if resp.json() fails
            return Response(
                {'error': f'Error parsing news API response: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            # Catch any other unexpected errors
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
