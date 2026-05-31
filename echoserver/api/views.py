from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from .serializers import SubjectSerializer
from main.models import Subject


class PingView(APIView):
    """Простой view для проверки работоспособности API"""

    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'message': 'API is up'})


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = []
