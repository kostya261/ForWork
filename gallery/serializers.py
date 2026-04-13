from rest_framework import serializers
from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.ImageField(source='image', read_only=True)

    class Meta:
        model = Image
        fields = ['id', 'title', 'image', 'image_url', 'uploaded_by', 'created_at']
        read_only_fields = ['uploaded_by', 'created_at']