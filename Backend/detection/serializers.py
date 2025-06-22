from rest_framework import serializers
from .models import UploadHistory
from django.contrib.auth.models import User

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)

class UploadSerializer(serializers.Serializer):
    image = serializers.FileField()
    password = serializers.CharField(required=False, allow_blank=True)

    def validate_image(self, file):
        allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
        if file.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type.")
        return file

class HistorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadHistory
        fields = ['id', 'image_url', 'result', 'confidence', 'timestamp', 'detection_details']
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None