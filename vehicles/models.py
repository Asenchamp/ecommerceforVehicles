from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models.signals import post_delete
from django.dispatch import receiver


# Create your models here.

# --- custom user model---
class CustomUser(AbstractUser):
    # inherit the default abstract user and it just misses these
    phone_number = models.CharField(max_length=14, unique=True)
    address = models.CharField(max_length=50)

    account_status_choices = (
        ('active','Active'),
        ('suspended','Suspended'),
    )

    account_status = models.CharField(max_length=10, choices=account_status_choices,default='active')

    # groups = None
    # user_permissions = None

    # New field for verification status
    verified = models.BooleanField(default=False)  # Defaults to False
    
    def __str__(self): # returns the username for a readable representation
        return self.username
    

# --- Make represents the vehicle manufactures ----
class Make(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name
    
# --- vehicle model associated with a particular make ---
class Model(models.Model):
    make = models.ForeignKey(Make, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    class Meta:
        unique_together = (("make","name"),)

    def __str__(self):
        return f"{self.make.name} >> {self.name}"
    
# --- key features for vehicles ---
class KeyFeatures(models.Model):
    feature = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.feature
    
# --- vehicles model--- 
class Vehicle(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    make = models.ForeignKey(Make, on_delete=models.PROTECT)
    model = models.ForeignKey(Model, on_delete=models.PROTECT)
    year = models.IntegerField(
        validators=[
            MinValueValidator(1886),
            MaxValueValidator(datetime.date.today().year)
        ],
        null=True, blank=True
    )
    color_choices = (
        ('RED','Red'),('WHITE','White'),
        ('BLACK','Black'),('GREY','Grey'),
    )
    color = models.CharField(max_length=15, choices=color_choices)
    interior_color = models.CharField(max_length=15, choices=color_choices)
    condition_choices = (
        ('BRAND NEW','Brand New'),
        ('USED','Used'),
    )
    condition = models.CharField(max_length=15, choices=condition_choices)
    transmission_choices = (
        ('AUTOMATIC','Automatic'),
        ('MANUAL','Manual'),
    )
    transmission = models.CharField(max_length=15, choices=transmission_choices)
    description = models.TextField()
    sale_rent_choices = (
        ('SALE','Sale'),('RENT','Rent'),
    )
    for_sale_or_rent = models.CharField(max_length=15, choices=sale_rent_choices)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    rate_choices = (
        ('DAILY','Daily'),('WEEKLY','Weekly'),
        ('MONTHLY','Monthly'),('YEARLY','Yearly'),
    )
    rate = models.CharField(max_length=15, choices=rate_choices, blank=True)
    fuel_choices = (
        ('DIESEL','Diesel'),('PETROL','Petrol'),
        ('SOLAR','Solar')
    )
    fuel_type = models.CharField(max_length=15, choices=fuel_choices)
    key_features = models.ManyToManyField(KeyFeatures, through='Vehiclekeyfeatures')

    def __str__(self):
        return f"{self.make.name} {self.model.name} ({self.year})"
    

# -- vehicle key features model --
class Vehiclekeyfeatures(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    feature = models.ForeignKey(KeyFeatures, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('vehicle','feature'),)

    def __str__(self):
        return f"{self.vehicle} - {self.feature}"
    
# --- type of spare part ----
class PartType(models.Model):
    name = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name
    
# ---  sub type of spare paret ---
class SubType(models.Model):
    type = models.ForeignKey(PartType, on_delete=models.CASCADE)
    name = models.CharField(max_length=15)

    class Meta:
        unique_together = (("type","name"),)
    
    def __str__(self):
        return f"{self.type.name} - {self.name}"
    
class SparePart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    make = models.ForeignKey(Make, on_delete=models.PROTECT)
    model = models.ForeignKey(Model, on_delete=models.PROTECT)
    type = models.ForeignKey(PartType, on_delete=models.PROTECT)
    subtype = models.ForeignKey(SubType, on_delete=models.PROTECT)
    condition_choices = (
        ('BRAND NEW','Brand New'),
        ('USED','Used'),
    )
    condition = models.CharField(max_length=15, choices=condition_choices)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])

    def __str__(self):
        return self.title
    
# -- type of service ---
class TypeOfService(models.Model):
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return self.name
    
class SubTypeOfService(models.Model):
    type_of_service = models.ForeignKey(TypeOfService, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    class Meta:
        unique_together = (("type_of_service","name"),)
    def __str__(self):
        return f"{self.type_of_service.name} - {self.name}"
    
class Service(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    type_of_service = models.ForeignKey(TypeOfService, on_delete=models.CASCADE)
    description = models.TextField()
    start_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    sub_services = models.ManyToManyField(SubTypeOfService, through='ServiceSubTypeOfService')

    def __str__(self):
        return f"{self.type_of_service.name} by {self.user.username}"
    
class ServiceSubTypeOfService(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    sub_type_of_service = models.ForeignKey(SubTypeOfService, models.CASCADE)

    class Meta:
        unique_together = (("service","sub_type_of_service"),)
    def __str__(self):
        return f"{self.service} - {self.sub_type_of_service.name}"
    
class Image(models.Model):
    entity_choices = (
        ('Users','Users'),('Vehicle','Vehicle'),
        ('Spareparts','Spareparts'),('Service','Service'),
    )
    image_path = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=15, choices=entity_choices)
    entity_id = models.PositiveIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}"
    
    def delete(self, *args, **kwargs):
        #delete file from the filesystem if it exists
        file_path = os.path.join(settings.MEDIA_ROOT, self.image_path)
        if default_storage.exists(self.image_path):
            default_storage.delete(self.image_path)
        super().delete(*args, **kwargs)


#signal handler for deletion
@receiver(post_delete, sender=Vehicle)
def delete_vehicle_related_images(sender, instance, **kwargs):
    #query images with entity_type 'Vehicle' and matching entity_id
    related_images = Image.objects.filter(entity_type='Vehicle', entity_id=instance.id)
    for img in related_images:
        img.delete()
    







    



