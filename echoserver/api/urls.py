from django.urls import path
from .views import PingView, SubjectListView

urlpatterns = [
    path('ping/', PingView.as_view(), name='api-ping'),
    path('subjects/', SubjectListView.as_view(), name='api-subjects'),
]
