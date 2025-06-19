from django.db import models
from django.contrib.auth.models import User

class Detection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detections')
    image = models.ImageField(upload_to='detections/')
    result = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.result}'
