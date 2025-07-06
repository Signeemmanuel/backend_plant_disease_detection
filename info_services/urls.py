from django.urls import path
from .views import WeatherAPIView, NewsAPIView

urlpatterns = [
    path('weather/current/', WeatherAPIView.as_view(), name='weather_current'),
    path('news/agriculture/', NewsAPIView.as_view(), name='news_agriculture'),
] 