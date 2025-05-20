from django.urls import path
from .views import CreateRestaurantView ,getOwnedRestaurants ,getNearestRestaurants, deleteRestaurant ,updateRestaurant, createMenu ,getOwnedMenus ,deleteMenu, updateMenu, getUploadImageURL ,getImageURL, getMenu ,toggleRestaurantActivateStatus

urlpatterns = [
    path('create' , CreateRestaurantView.as_view()), 
    path('list' , getOwnedRestaurants.as_view()), 
    path('delete' , deleteRestaurant.as_view()), 
    path('update' , updateRestaurant.as_view()), 
    path('menu/create' , createMenu.as_view()), 
    path('menu/list' , getOwnedMenus.as_view()), 
    path('menu/delete' , deleteMenu.as_view()), 
    path('menu/update' , updateMenu.as_view()), 
    path('get-image-upload' , getUploadImageURL.as_view()), 
    path('menu/get' , getMenu.as_view()), 
    path('restaurant/toggle-activation' , toggleRestaurantActivateStatus.as_view()), 
    path('get-image-url' , getImageURL.as_view()), 
    path('get-nearest' , getNearestRestaurants.as_view()), 
    
]