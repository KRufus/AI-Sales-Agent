from django.urls import path
from ai_agent import views
from django.urls import re_path

urlpatterns = [
    path("make-call/", views.make_ai_call, name="make_ai_call"),
    # path('greet-client/', views.greet_client, name='greet_client'),
    # path("thank-you/", views.play_ai_response_with_thank_you, name="thank_you"),
    # path("process-gather/", views.process_gather, name="process_gather"),
    # path("play-ai-response/", views.play_ai_response, name="play_ai_response"),
    path(
        "make-call-in-celery/",
        views.make_ai_call_in_celery,
        name="make_ai_call_in_celery",
    ),
    path("twiml/", views.get_twiml, name="get_twiml"),
]
