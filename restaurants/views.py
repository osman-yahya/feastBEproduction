from dotenv import load_dotenv
import os
from .serializer import RestaurantSerializer, MenuSerializer
from rest_framework.views import APIView
from users.models import User
from .models import Restaurant, Menu
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
import time
from dotenv import load_dotenv
import os
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

load_dotenv()
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_REFRESH_SECRET_KEY = os.getenv('JWT_REFRESH_SECRET_KEY')

class CreateRestaurantView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        serializer = RestaurantSerializer(data=request.data, context={'user': user})  # Context ile `userid` geç
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "success", "userid": user.id , "restaurantid" : serializer.instance.id})

class getOwnedRestaurants(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user        
        restaurants = Restaurant.objects.filter(owner=user)
        if not restaurants or restaurants == [] or restaurants == None :
            return Response({"message" : "No restaurant found"})
        serializer = RestaurantSerializer(restaurants, many=True)
        return Response(serializer.data)
    
class getNearestRestaurants(APIView):
    def post(self, request):
        xaxs = request.data.get("xaxis")
        yaxs = request.data.get("yaxis")
        if not (xaxs and yaxs):
            return Response({"message" : "wrong type of request"})
        try:
            user_location = Point(float(xaxs), float(yaxs), srid=4326)
        except ValueError:
            return Response({"message": "wrong type of parameters, make sure request has xaxs,yaxs parameters"}, status=400)
        restaurants = Restaurant.objects.filter(
        is_active=True,
        location__isnull=False,
        location__distance_lte=(user_location, D(km=10))
        ).annotate(
        distance=Distance('location', user_location)
        ).order_by('distance')[:50]
        serializer = RestaurantSerializer(restaurants,many=True)
        return Response(serializer.data)

class deleteRestaurant(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        try:
            deleteid = request.data.get("restaurant_id")
            if (not deleteid) or deleteid == None : 
                return Response({"message" : "need to include 'restaurant_id' "} , status=404)
            restaurant = Restaurant.objects.get(id=deleteid)
            if restaurant.owner != user:
                raise AuthenticationFailed("User is not the owner of the restaurant")
        except Restaurant.DoesNotExist:
            return Response({"message" : "no restaurant found"} , status=404)
        restaurant.delete()
        return Response({"message" : "deleted successfully"})
        
class updateRestaurant(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        try :
            restaurant = Restaurant.objects.get(id = request.data.get("id"))
        except Restaurant.DoesNotExist:
            Response({"message" : "restaurant does not exists"} , status= 404)
        except Exception as e:
            return Response({"message" : f"bad request : {e}"} , status=400)
        if restaurant.owner != user:
            raise AuthenticationFailed("user is not the actual owner.")
        
        newaddress = request.data.get("address")
        newabout = request.data.get("about")
        newphone = request.data.get("phone")
        newprofilepic = request.data.get("profile_picture")
        newmenu = request.data.get("menu")

        if newmenu : 
            try :
                menu = Menu.objects.get(id=newmenu)
                if menu.owner != user:
                    raise AuthenticationFailed("user is not owned the menu")
                restaurant.menu = menu
            except Menu.DoesNotExist:
                return Response({"message" : "menu does not exists"} , status= 404)
            except Exception as e:
                return Response({"message" : f"bad request : {e}"} , status=400)
            
        if newaddress:
            restaurant.address = newaddress
        if newabout:
            restaurant.about = newabout
        if newphone:
            restaurant.phone = newphone
        if newprofilepic:
            if newprofilepic == "default":
                restaurant.profile_picture = 'restaurant_pictures/default.jpeg'
            elif newprofilepic == "keep":
                pass
            else:
                restaurant.profile_picture = newprofilepic
        restaurant.save()
        return Response({"message" : "successfully changed."})

class createMenu(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)

        serializer = MenuSerializer(data=request.data, context={'user': user})  # Context ile `userid` geç
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "success", "userid": user.id , "menuid" : serializer.instance.id})

class getOwnedMenus(APIView):
    permission_classes = [IsAuthenticated]    
    def get(self,request):
        user = request.user
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        menulist = Menu.objects.filter(owner=user)
        if not menulist or menulist == [] or menulist == None :
            return Response({"message" : "No menus found"})
        serializer = MenuSerializer(menulist,many=True)
        return Response(serializer.data)

class deleteMenu(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user    
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        try:
            deleteid = request.data.get("menu_id")
            if (not deleteid) or deleteid == None : 
                return Response({"message" : "need to include 'menu_id' "} , status=404)
            menu = Menu.objects.get(id=deleteid)
            if menu.owner != user:
                raise AuthenticationFailed("User is not the owner of the restaurant")
        except Restaurant.DoesNotExist:
            return Response({"message" : "no restaurant found"} , status=404)
        menu.delete()
        return Response({"message" : "deleted successfully"})

class updateMenu(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        menuid = request.data.get("id")
        try :
            menu = Menu.objects.get(id = menuid)
        except Menu.DoesNotExist:
            return Response({"message" : "menu not found"}, status=404)
        if menu.owner != user:
            raise AuthenticationFailed("menus owner is not authenticated")
        serializer = MenuSerializer(menu, data=request.data, context={'user': user})
        if serializer.is_valid():
            menu = serializer.save()  # Menu nesnesini güncelleriz
            return Response({"message": "successfully updated", "userid": user.id, "menuid" : menu.id})
        else:
            return Response(serializer.errors, status=400)
        
class getUploadImageURL(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user=request.user  
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        file_key = ""
        try:
            upload_type = request.data.get("type")
            
            match upload_type:
                case 'menu_image':
                    file_key = f"menu_pictures/{user.id % 50}/{user.id}/{int(time.time()*1000)}.jpeg"
                case 'item_image':
                    file_key = f"item_pictures/{user.id % 50}/{user.id}/{int(time.time()*1000)}.jpeg"
                case 'restaurant_picture':
                    restaurantid = request.data.get("id")
                    if restaurantid != None or restaurantid != "":
                        try:
                            restaurant = Restaurant.objects.get(id=restaurantid)
                            if restaurant.owner != user:
                                raise AuthenticationFailed("user is not the owner of restaurant")
                        except Restaurant.DoesNotExist:
                            return Response({"message": "restaurant with given id does not exists"}, status=404)

                    file_key = f"restaurant_pictures/{restaurantid % 50}/{int(time.time()*1000)}.jpeg"
                    restaurant.profile_picture = file_key
                    restaurant.save()
                case _:
                    return Response({"message" : "request must specify 'type' attiribute"},status=400)
                
        except:
            return Response({"message" : "bad request : check 'type' attiribute"},status=400)

        
        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_S3_REGION_NAME,config=Config(signature_version='s3v4'))

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        try :
            url = s3_client.generate_presigned_url(
                'put_object',
                Params = {'Bucket' : bucket_name, 'Key' : file_key, 'ContentType': 'image/jpeg'},
                ExpiresIn = 3600
            )
            return Response({
                'image-adress' : file_key ,
                'presigned-url-for-profile-pic' : url ,
                'message' : 'do not forget to save image-adress!'
                })
        
        except NoCredentialsError:
            return Response({'error' : 'AWS credentials not found -server error-'} , status=400)
        
        except Exception as e:
            return Response({'error': f'Error generating presigned URL: {str(e)}'}, status=500)

class getImageURL(APIView):
    def post(self,request):
        address = request.data.get("address")
        if address == None or address == "":
            return Response({"message": "request has no attribute 'address'"},status=400)
        
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
                    'Key': address  # Dosya yolunu modelden al
                },
                ExpiresIn=3600  # 1 saat geçerli
            )
            return Response({"url" : url})
        except Exception as e:
            # Hata durumunda None dön
            return Response({"message" : f"failed to get image:  ({str(e)})"},status=500)

class getMenu(APIView):
    def post(self,request):
        menuid = request.data.get("id")
        restaurant_id = request.data.get("restaurant_id")
        
        if menuid == None :
            return Response({"message" : "menuid attiribute has not provided" },status=404)
        try:
            url = ""
            if restaurant_id is not None :
                try:
            # S3 client konfigürasyonu
                    restaurant = Restaurant.objects.get(id = restaurant_id)
                    if restaurant is None:
                        raise Exception("Restaurant does not exists.")
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
                            'Key': restaurant.profile_picture.name  # Dosya yolunu modelden al
                        },
                        ExpiresIn=3600  # 1 saat geçerli
                    )
                 
                except Exception as e:
                    
                    return Response({"message" : f"error occured when calling restaurant image url : {e}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            menu = Menu.objects.get(id=menuid)
            serializer = MenuSerializer(menu)
            return Response({
                "restaurant_img" : url if url else "",
                "menu" : serializer.data
            })
        except Menu.DoesNotExist:
            return Response({"message" : "menu not found" },status=404)

class toggleRestaurantActivateStatus(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.isRestaurant == False:
            return Response({"message" : "user is not defined as restaurant"}, status=403)
        try :
            restaurant = Restaurant.objects.get(id = int(request.data.get("id")))
        except Restaurant.DoesNotExist:
            return Response({"message" : "no restaurant with id"} , status=404)
        except Exception as e:
            return Response({"message" : f"bad request : {e}"} , status=400)

        if restaurant.owner != user:
            raise AuthenticationFailed("user is not the actual owner.")
            
        if restaurant.is_active == True:
            restaurant.is_active = False
            restaurant.save()
            return Response({"message" : "successfully deactivated."})
        else:
            menucheck = restaurant.menu is None
            addresscheck = not restaurant.address  # Boş string veya None ise True olur
            aboutcheck = not restaurant.about  # Boş string veya None ise True olur
            phonecheck = not restaurant.phone
                
            if menucheck or addresscheck or aboutcheck or phonecheck:
                return Response({
                    "message" : "error : there exists blank fields",
                    "blankfields" : f"{"menu" if menucheck else ""} {"address" if addresscheck else ""} {"phone" if phonecheck else ""} {"about" if aboutcheck else ""}"
                    },status=406)
                
            else: 
                restaurant.is_active = True
                restaurant.save()
                return Response({"message" : "successfully activated."})
            
