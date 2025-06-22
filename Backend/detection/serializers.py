from rest_framework import serializers
from .models import UploadHistory
from django.contrib.auth.models import User

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)

class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadHistory
        fields = ['image']

class HistorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UploadHistory
        fields = ['id', 'image_url', 'result', 'confidence', 'timestamp']
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None