from django.urls import path
from ai_agent import views

urlpatterns = [
    path('make-call/', views.make_ai_call, name='make_ai_call'), 
    # path('greet-client/', views.greet_client, name='greet_client'),
    # path('gather-input/', views.gather_input, name='gather_input'),
    path('process-gather/', views.process_gather, name='process_gather'),
    # path('process-recording/', views.process_recording, name='process_input'),
    path('make-call-in-celery/', views.make_ai_call_in_celery, name='make_ai_call_in_celery'),
]
