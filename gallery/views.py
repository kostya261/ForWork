from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Image
from .serializers import ImageSerializer
import hashlib


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        # Проверяем файл
        uploaded_file = request.FILES.get('image')
        if uploaded_file:
            # Вычисляем хеш
            hasher = hashlib.sha256()
            for chunk in uploaded_file.chunks():
                hasher.update(chunk)
            file_hash = hasher.hexdigest()

            # Проверяем, существует ли уже такой файл
            existing = Image.objects.filter(file_hash=file_hash).first()
            if existing:
                # Возвращаем существующий объект
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

            # Сбрасываем указатель файла для повторного чтения
            uploaded_file.seek(0)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Вычисляем хеш перед сохранением
        uploaded_file = self.request.FILES.get('image')
        if uploaded_file:
            uploaded_file.seek(0)
            hasher = hashlib.sha256()
            for chunk in uploaded_file.chunks():
                hasher.update(chunk)
            file_hash = hasher.hexdigest()
            serializer.save(uploaded_by=self.request.user, file_hash=file_hash)
        else:
            serializer.save(uploaded_by=self.request.user)