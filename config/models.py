from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TwilioConfig(models.Model):
    label = models.CharField(max_length=100)
    twilio_no = models.CharField(max_length=20)
    account_sid = models.CharField(max_length=255)
    auth_token = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='twilio_configs', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label
