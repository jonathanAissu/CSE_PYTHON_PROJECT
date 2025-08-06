from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractUser #extending the super user model for us to create our own user



# Create your models here.
class UserProfile(AbstractUser):
    is_salesagent = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    phone = models.CharField(max_length=15)
    title = models.CharField(max_length=10)
    username = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return str(self.username)
    
    class Meta:
        db_table = "home_users"
        verbose_name = "User"
        verbose_name_plural = "Users"

class Stock(models.Model):
    CHICK_TYPE_CHOICES = [
        ('Broilers', 'Broilers'),
        ('Layers', 'Layers'),
    ]
    
    CHICK_BREED_CHOICES = [
        ('local', 'Local'),
        ('exotic', 'Exotic'),
    ]
    
    stock_name = models.CharField(max_length=100, help_text="Mixture of characters & numbers")
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    date_added = models.DateTimeField(auto_now_add=True)
    chick_type = models.CharField(max_length=10, choices=CHICK_TYPE_CHOICES)
    chick_breed = models.CharField(max_length=10, choices=CHICK_BREED_CHOICES)
    price = models.IntegerField(default=1650, help_text="Price in UGX")
    manager_name = models.CharField(max_length=100, help_text="Name of the manager who registered the stock")
    chicks_period = models.IntegerField(validators=[MinValueValidator(0)], help_text="Age in days")
    
    def __str__(self):
        return f"{self.stock_name} - {self.chick_type}"


class Feedstock(models.Model):
    name_of_feeds = models.CharField(max_length=100)
    quantity_of_feeds = models.IntegerField(validators=[MinValueValidator(0)], help_text="Number of bags")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    type_of_feeds = models.CharField(max_length=50)
    brand_of_feeds = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    supplier_name = models.CharField(max_length=100)
    supplier_contact = models.CharField(max_length=20)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum price of a bag of feeds")
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name_of_feeds} - {self.brand_of_feeds}"


class Farmer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    FARMER_TYPE_CHOICES = [
        ('starter', 'Starter'),
        ('returning', 'Returning'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    farmer_name = models.CharField(max_length=100, help_text="All names")
    farmer_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    nin = models.CharField(max_length=14, unique=True, help_text="National Identification Number")
    recommender_name = models.CharField(max_length=100)
    recommender_nin = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    farmer_age = models.IntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(30)],
        help_text="Age between 18 and 30"
    )
    type_of_farmer = models.CharField(max_length=10, choices=FARMER_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', help_text="Approval status")
    date_registered = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.farmer_name} ({self.status})"


class ChickRequest(models.Model):
    CHICK_TYPE_CHOICES = [
        ('Broilers', 'Broilers'),
        ('Layers', 'Layers'),
    ]
    
    CHICK_BREED_CHOICES = [
        ('local', 'Local'),
        ('exotic', 'Exotic'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('sold', 'Sold'),
    ]
    
    YES_NO_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
    ]
    
    farmer_name = models.ForeignKey(Farmer, on_delete=models.CASCADE)
    chicks_type = models.CharField(max_length=10, choices=CHICK_TYPE_CHOICES)
    chicks_breed = models.CharField(max_length=10, choices=CHICK_BREED_CHOICES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)], help_text="Quantity of chicks")
    date_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feeds_needed = models.CharField(max_length=1, choices=YES_NO_CHOICES, help_text="Took the feeds")
    chicks_period = models.IntegerField(validators=[MinValueValidator(0)], help_text="Age in days")
    delivered = models.CharField(max_length=1, choices=YES_NO_CHOICES, default='N')
    sales_authorized = models.BooleanField(default=False, help_text="Sales agent authorized the sale")
    sales_authorized_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, help_text="Sales agent who authorized the sale")
    sales_authorized_date = models.DateTimeField(null=True, blank=True, help_text="Date when sale was authorized")
    
    def __str__(self):
        return f"Request by {self.farmer_name} - {self.chicks_type} ({self.status})"
