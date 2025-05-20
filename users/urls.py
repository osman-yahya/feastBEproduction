from django.urls import path
from .views import SignUpView,LoginView,GetCredentials,SignOutView,getPresignedURLforProfilePictureUpload,getAnyUserInfo,updateUserCredentials,PasswordResetRequestView,PasswordResetConfirmView
urlpatterns = [
    path('signup' , SignUpView.as_view()), 
    path('login' , LoginView.as_view()), 
    path('self' , GetCredentials.as_view()), 
    path('logout' , SignOutView.as_view()), 
    path('get-upload-img-url' , getPresignedURLforProfilePictureUpload.as_view()), 
    path('other' , getAnyUserInfo.as_view()), 
    path('update' , updateUserCredentials.as_view()),    

    path('reset-password' , PasswordResetRequestView.as_view()),    
    path('confirm-password' , PasswordResetConfirmView.as_view()),    

]