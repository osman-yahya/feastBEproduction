from rest_framework import serializers
from .models import Menu, Restaurant, Item, Category
from rest_framework import serializers
from django.conf import settings
import boto3
from botocore.client import Config

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'price', 'item_picture', 'isHalal', 'isVegan', 'isGlutenFree']
        extra_kwargs = {
            'item_picture': {'required': False, 'allow_null': True,'write_only': True} 
        }

class CategorySerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True)  # Her kategori altındaki öğeleri serileştiriyoruz

    class Meta:
        model = Category
        fields = ['id', 'name', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        category = Category.objects.create(**validated_data)
        for item_data in items_data:
            Item.objects.create(category=category, **item_data)
        return category


class MenuSerializer(serializers.ModelSerializer):
    content = serializers.JSONField()  # İçeriği JSON olarak saklayacağız

    class Meta:
        model = Menu
        fields = ['id', 'owner', 'name', 'content']
        extra_kwargs = {'owner': {'read_only': True}}

    def validate_content(self, value):
        """
        JSON içeriğini doğrulamak için custom bir validate metodu.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Content must be a dictionary.")

        categories = value.get("categories", [])
        if not isinstance(categories, list):
            raise serializers.ValidationError("Categories must be a list.")

        category_serializer = CategorySerializer(data=categories, many=True)
        if not category_serializer.is_valid():
            raise serializers.ValidationError(category_serializer.errors)

        return value

    def create(self, validated_data):
        user = self.context['user']
        menu = Menu.objects.create(owner=user, **validated_data)
        return menu



class RestaurantSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField(read_only = True)
    class Meta:
        model = Restaurant
        fields = ['id', 'owner', 'name', 'address', 'location', 'about', 'phone', 'profile_picture', 'menu', 'profile_picture_url', 'is_active']
        extra_kwargs = {
            'owner': {'read_only': True},
            'profile_picture': {'write_only': True}
            }  # `owner` dışarıdan değiştirilemez

    def get_profile_picture_url(self, obj):
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
        user = self.context['user']  # `CreateRestaurantView` içinde `context` olarak gönderilen kullanıcıyı al
        restaurant = Restaurant.objects.create(owner=user, **validated_data)
        return restaurant
