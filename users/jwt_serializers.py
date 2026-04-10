from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserMeSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Расширенный сериализатор для JWT — добавляем данные пользователя в ответ"""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Добавляем данные пользователя в ответ
        user = self.user
        data['user'] = UserMeSerializer(user).data

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer