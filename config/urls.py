from django.urls import path
from .views import TwilioConfigurationList, TwilioConfigurationDetail

urlpatterns = [
    path('', TwilioConfigurationList.as_view(), name='twilio-configuration-list'),
    path('<int:id>/', TwilioConfigurationDetail.as_view(), name='twilio-configuration-detail'),
]
