from django.db import models
from django.contrib.auth.models import User

class UploadHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')
    result = models.CharField(max_length=10)
    confidence = models.FloatField()
    detection_details = models.JSONField(default=dict)  # <-- Add this line
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
