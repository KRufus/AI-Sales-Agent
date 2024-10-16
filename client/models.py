from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()

# creating a new client instance
class Client(models.Model):

    STATUS_PENDING = 0
    STATUS_ONGOING = 1
    STATUS_CANCELLED = 2
    STATUS_COMPLETED = 3

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ONGOING, 'Ongoing'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
    ]
    
    
    name = models.CharField(max_length=255)
    phone_number = PhoneNumberField(unique=True)  
    call_status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING) 
    is_called = models.BooleanField(default=False)

    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

    class Meta:
        indexes = [
            models.Index(fields=['call_status']),
            models.Index(fields=['created_by']),
        ]
        
