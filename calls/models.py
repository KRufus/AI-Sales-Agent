from django.db import models
from django.contrib.auth import get_user_model
from assistant.models import Assistant

User = get_user_model()

class Call(models.Model):
    id = models.AutoField(primary_key=True)
    session_name = models.CharField(max_length=255)
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_phone = models.CharField(max_length=20, null=True, blank=True)
    consent = models.BooleanField(default=False, null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.session_name

class Log(models.Model):
    id = models.AutoField(primary_key=True)
    call = models.ForeignKey(Call, related_name='logs', on_delete=models.CASCADE)
    user = models.CharField(max_length=100)  # Can be 'Sys' or 'client'
    message = models.TextField()
    # time = models.DateTimeField(auto_now_add=True)
    


    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Log for {self.call.session_name} by {self.user}"
    
    class Meta:
        ordering = ['created_on']
