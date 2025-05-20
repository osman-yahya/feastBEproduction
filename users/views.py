from .models import User
from rest_framework.views import APIView
from .serializer import UserSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
import boto3
from django.contrib.auth import authenticate
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny # ilerde staff control panel için isStaff permission gerekecek. -> BasePermission
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string

class SignUpView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Kullanıcıyı kaydet
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request, format=None):
        email = request.data.get('email')
        password = request.data.get('password')

        # Kullanıcıyı authenticate et
        user = authenticate(request, email=email, password=password)

        if user is not None:
            # JWT token oluştur
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Token'ları cookie olarak gönder
            response = Response({
                'message': 'Giriş başarılı',
                'user_id': user.id,
                'email': user.email,
            })

            # Access Token Çerez Ayarı
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=access_token,
                httponly=True,   # JS erişemesin
                secure=True,     # HTTPS için True olmalı
                samesite='None', # CORS için gerekli
                max_age=60*60*24*60
            )

            # Refresh Token Çerez Ayarı
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite='None',
                max_age=60*60*24*60
            )

            return response
        else:
            return Response({'message': 'Geçersiz kimlik bilgileri'}, status=400)
    
class GetCredentials(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
   
class SignOutView(APIView):
    def post(self, request):
        # Çıkış işlemi için yanıt oluştur
        response = Response({'message': 'Çıkış Yapıldı'})

        # Çerezleri silme işlemi (her iki yöntemle silme)
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'], path='/')
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        response.delete_cookie('csrftoken', path='/')
        response.delete_cookie('sessionid', path='/')

        # Çerezlerin süresini geçmiş bir tarihe ayarlayarak silme işlemi
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value="",
            expires=now() ,
            secure=True,  # HTTPS için True olmalı
            httponly=True,  # JS erişemesin
            samesite="None"
        )

        # Refresh token'ı çereze yaz
        response.set_cookie(
            key="refresh_token",
            value="",
            expires=now() ,
            secure=True,
            httponly=True,
            samesite="None"
        )

        # Kullanıcıyı anonim yaparak middleware'e engel olun
        request.user = None  # Kullanıcıyı anonim yapıyoruz

        # Authorization header'ı temizleyin, eski token'ların gönderilmesini engelleyin
        response["Authorization"] = "Bearer "  # Auth header'ı temizliyoruz

        return response
   
#use with post request, after uploading your picture, insert in to the database via setProfilePictureAdressToUser
class getPresignedURLforProfilePictureUpload(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):


        user = request.user

        s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, region_name=settings.AWS_S3_REGION_NAME,config=Config(signature_version='s3v4'))

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        file_key = f"profile_pictures/{user.id % 100}/{user.id}.jpeg"  # Kullanıcı id'sine göre dosya adı belirlenir

        try :
            url = s3_client.generate_presigned_url(
                'put_object',
                Params = {'Bucket' : bucket_name, 'Key' : file_key, 'ContentType': 'image/jpeg'},
                ExpiresIn = 3600
            )
            return Response({
                'presigned-url-for-profile-pic' : url,
                'path' : file_key,
                'message' : "after saving image, update user profile picture with 'path'."
                })

        except NoCredentialsError:
            return Response({'error' : 'AWS credentials not found -server error-'} , status=400)
        
        except Exception as e:
            return Response({'error': f'Error generating presigned URL: {str(e)}'}, status=500)
        
#include your url in your response data with key : 'image-url'
class getAnyUserInfo(APIView):
    def post(self,request):
        user_id = request.data.get('user_id')
        if not user_id:
            Response({'error' : 'you need to specify userid in request.data with key : user_id'} , status=400)

        try :
            user = User.objects.get(id=int(user_id))  # get() ile kullanıcıyı alıyoruz
        
            serializer = UserSerializer(user)
            return Response(serializer.data , status=200)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404) 

        except Exception as e:
            return Response({'error': f'{e}'}, status=400)       

#use with post method,
class updateUserCredentials(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = request.user
        new_about = request.data.get('about')
        new_firstname = request.data.get('first-name')
        new_lastname = request.data.get('last-name')
        current_pass = request.data.get('password')
        new_pass = request.data.get('new-password')
        profile_pic_url = request.data.get('profile_pic')
        
        if new_about:
            user.about = new_about
        if new_firstname:
            user.first_name = new_firstname
        if new_lastname:
            user.last_name = new_lastname
        if profile_pic_url:
            if profile_pic_url == "default":
                user.profile_picture = 'profile_pictures/default.jpeg'
            elif profile_pic_url == "set":
                user.profile_picture = f"profile_pictures/{user.id % 100}/{user.id}.jpeg"
        if new_pass:
            if user.check_password(current_pass):
                user.set_password(new_pass)
            else:
                raise AuthenticationFailed("to change password, you must give current password correctly")

        user.save()
        return Response({"message": "User information updated successfully."}, status=200)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Request a password reset
        """
        data = request.data
        email = data.get('email', '')
        
        if not email:
            return Response(
                {"error": "Email is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find user with this email
        try:
            # Use get() when expecting one result rather than filter().first()
            user = User.objects.get(email=email)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL for the React frontend
            reset_url = f"{settings.PASSWORD_RESET_URL}/{uid}/{token}"
            
            # Context for email template
            context = {
                'user': user,
                'reset_url': reset_url,
                'site_name': 'feast',
            }
            
            # Render email content
            email_subject = "Şifre Yenileme İsteği - feast"
            email_body_html = render_to_string('user/reset-password/password_reset_email.html', context)
            email_body_text = render_to_string('user/reset-password/password_reset_email.txt', context)
            
            # Send email through AWS SES
            send_mail(
                subject=email_subject,
                message=email_body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=email_body_html,
            )
            
            return Response(
                {"success": "If that email exists in our system, a password reset link has been sent."},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            return Response(
                {"success": "If that email exists in our system, a password reset link has been sent."},
                status=status.HTTP_200_OK
            )
            



class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Set new password with valid token
        """
        data = request.data
        uid = data.get('uid', '')
        token = data.get('token', '')
        new_password = data.get('new_password', '')
        
        if not uid or not token or not new_password:
            return Response(
                {"error": "UID, token and new password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Decode the uid
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            # Check if token is valid
            if default_token_generator.check_token(user, token):
                # Set new password
                user.set_password(new_password)
                user.save()
                
                return Response(
                    {"success": True, "message": "Password has been reset successfully"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Token is invalid or expired"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid user ID or token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )