from django.db import models
from django.contrib.auth import get_user_model # More robust way to get the User model
from cloudinary.models import CloudinaryField # Import CloudinaryField

User = get_user_model()
class Detection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detections')
    image = CloudinaryField('image') # 'image' is a common default for CloudinaryField
    # image = models.ImageField(upload_to='detections/')    
    result = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.result}'
    
    class Meta:
        # Optional: Add a verbose name for the admin interface or documentation
        verbose_name = "Plant Detection"
        verbose_name_plural = "Plant Detections"
        # Optional: Order detections by creation time by default
        ordering = ['-created_at']