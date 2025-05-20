from django.db import models
from django.contrib.gis.db import models as geoModel
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete
from django.dispatch import receiver

User = get_user_model()

class Menu(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=255)
    content = models.JSONField()  # Artık "context" değil, "content" olarak adlandırıldı.

    def __str__(self):
        return f"Menü ID: {self.id}, Owner user ID: {self.owner.id}"

# Option 2: Modifying the Restaurant model
# Replace your current Restaurant model with this

# Correct Restaurant model implementation
class Restaurant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurants')
    menu = models.ForeignKey(Menu, related_name='restaurants', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=60)
    address = models.TextField(blank=True, null=True)
    location = geoModel.PointField(srid=4326)
    about = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    
    # This is the correct field name
    is_active = models.BooleanField(default=False)
    
    profile_picture = models.ImageField(upload_to='restaurant_pictures/', 
                                       null=True, blank=True, 
                                       default='restaurant_pictures/default.jpeg')

    def __str__(self):
        return f"Restaurant: {self.name} at location {self.location}"
    
    def save(self, *args, **kwargs):
        # Enforce the business rule when saving
        if self.is_active and not self.menu:
            self.is_active = False
        
        super().save(*args, **kwargs)



@receiver(post_delete, sender=Menu)
def deactivate_restaurants_on_menu_delete(sender, instance, **kwargs):
    """
    When a menu is deleted, set all restaurants using this menu to inactive
    """
    Restaurant.objects.filter(menu_id=instance.id, is_active=True).update(is_active=False)



""" class Restaurant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurants')
    menu = models.ForeignKey(Menu, related_name='restaurants', on_delete=models.SET_NULL, null=True,blank=True)
    name = models.CharField(max_length=60)
    address = models.TextField(blank=True, null=True)
    location = geoModel.PointField(srid=4326)
    about = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    is_active= models.BooleanField(default=False)

    profile_picture = models.ImageField(upload_to='restaurant_pictures/', null=True, blank=True, default='restaurant_pictures/default.jpeg')

    def __str__(self):
        return f"Restaurant: {self.name} at location {self.location}" """


class Category(models.Model):
    menu = models.ForeignKey(Menu, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=40)


class Item(models.Model):
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    item_picture = models.CharField(default='item_pictures/default.jpeg', blank=True,null=True)
    isHalal = models.BooleanField( null=True ,blank=True ,default=False)
    isVegan = models.BooleanField( null=True ,blank=True ,default=False)
    isGlutenFree = models.BooleanField( null=True ,blank=True ,default=False)

    def __str__(self):
        return f"İsim: {self.name}, Kategori: {self.category.name}, Ait olduğu menü ID: {self.category.menu.id}"

