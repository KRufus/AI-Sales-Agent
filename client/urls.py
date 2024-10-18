from django.urls import path
from .views import ClientList, ClientDetail, ClientDelete, ClientCreateOrBulkCreate, ExecuteCalls

urlpatterns = [
    path('', ClientList.as_view(), name='client-list'),
    path('<int:id>/', ClientDetail.as_view(), name='client-detail'),
    path('<int:id>/delete/', ClientDelete.as_view(), name='client-delete'),
    path('create/', ClientCreateOrBulkCreate.as_view(), name='client-create'),
    path('execute-user-calls/', ExecuteCalls.as_view(), name='execute-user-calls'),
]
