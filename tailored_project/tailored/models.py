from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
import datetime

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    picture = models.ImageField(upload_to = "profile_images", blank = True)
    postcode = models.CharField(max_length = 8)
    rating = models.IntegerField(default = 0)
    phone = models.IntegerField(default = 0)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    title = models.CharField(max_length = 128, unique = True)

    class Meta:
        verbose_name_plural = "categories"
    
    def __str__(self):
        return self.title

class Brand(models.Model):
    brandName = models.CharField(max_length = 128, unique = True)

    def __str__(self):
        return self.brandName

class Item(models.Model):
    category = models.ForeignKey(Category)
    brand = models.ForeignKey(Brand)

    itemName = models.CharField(max_length = 128)
    itemID = models.IntegerField(default = 0)
    price = models.IntegerField(default = 0)

    itemPic = models.ImageField(upload_to = "item_images", blank = True)
    description = models.TextField(blank = True)
    datePosted = models.DateField(auto_now = True)
    
    sold = models.BooleanField(default = False)
    condition = models.CharField(max_length = 128, default = "")
    dailyVisits = models.IntegerField(default = 0)
    
    gender = models.CharField(max_length = 128)
    size = models.CharField(max_length = 128)
    ageGroup = models.CharField(max_length = 128, default = "")

    def __str__(self):
        return self.itemName