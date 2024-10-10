from django.urls import path
from .views import AssistantList, AssistantDetail

urlpatterns = [
    path('', AssistantList.as_view(), name='assistant-list'),
    path('<int:id>/', AssistantDetail.as_view(), name='assistant-detail'),
]
