from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from .models import TwilioConfig
from .serializers import TwilioConfigurationSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class TwilioConfigurationList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        configurations = TwilioConfig.objects.filter(created_by=request.user)
        serializer = TwilioConfigurationSerializer(configurations, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = TwilioConfigurationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TwilioConfigurationDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id, user):
        try:
            return TwilioConfig.objects.get(id=id, created_by=user)
        except TwilioConfig.DoesNotExist:
            return None

    def get(self, request, id):
        configuration = self.get_object(id, request.user)
        if configuration is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TwilioConfigurationSerializer(configuration)
        return JsonResponse(serializer.data)

    def put(self, request, id):
        configuration = self.get_object(id, request.user)
        if configuration is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = JSONParser().parse(request)
        serializer = TwilioConfigurationSerializer(configuration, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        configuration = self.get_object(id, request.user)
        if configuration is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        configuration.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
