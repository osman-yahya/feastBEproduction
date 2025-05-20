from rest_framework import serializers
from .models import User
from django.conf import settings
import boto3
from botocore.client import Config

class UserSerializer(serializers.ModelSerializer):
    # Yeni eklenen profil fotoğrafı URL alanı
    profile_picture_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'username', 
            'about', 
            'password', 
            'profile_picture', 
            'followers', 
            'isRestaurant', 
            'profile_picture_url'  # Yeni alan eklendi
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'profile_picture': {'write_only': True},  # Ham dosya yolunu gizle
            'email': {'write_only': True},  # Ham dosya yolunu gizle
        }

    def get_profile_picture_url(self, obj):
        """
        Profil fotoğrafı için presigned URL oluşturan özel metod
        """
        # Profil fotoğrafı yoksa None dön
        if not obj.profile_picture:
            return None
            
        try:
            # S3 client konfigürasyonu
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                config=Config(signature_version='s3v4')
            )
            
            # Presigned URL oluşturma
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': obj.profile_picture.name  # Dosya yolunu modelden al
                },
                ExpiresIn=3600  # 1 saat geçerli
            )
            return url
        except Exception as e:
            # Hata durumunda None dön
            return None

    def create(self, validated_data):
        #Kayıt işlemi için kullanılan metod
        
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance