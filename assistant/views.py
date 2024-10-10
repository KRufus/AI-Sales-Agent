from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from .models import Assistant
from .serializers import AssistantSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from config.models import TwilioConfig

class AssistantList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assistants = Assistant.objects.filter(created_by=request.user)
        serializer = AssistantSerializer(assistants, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request):
        data = JSONParser().parse(request)
        config_id = data.get('config')

        # Check if the config exists and belongs to the user
        try:
            if config_id:
                config = TwilioConfig.objects.get(id=config_id, created_by=request.user)
                data['config'] = config.id
        except TwilioConfig.DoesNotExist:
            return JsonResponse({'error': 'Config not found or not owned by you.'}, status=status.HTTP_400_BAD_REQUEST)


        serializer = AssistantSerializer(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssistantDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id, user):
        try:
            return Assistant.objects.get(id=id, created_by=user)
        except Assistant.DoesNotExist:
            return None

    def get(self, request, id):
        assistant = self.get_object(id, request.user)
        if assistant is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssistantSerializer(assistant)
        return JsonResponse(serializer.data)

    def put(self, request, id):
        assistant = self.get_object(id, request.user)
        if assistant is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = JSONParser().parse(request)
        config_id = data.get('config')

        if config_id:
            # Check if the config exists and belongs to the user
            try:
                config = TwilioConfig.objects.get(id=config_id, created_by=request.user)
            except TwilioConfig.DoesNotExist:
                return JsonResponse({'error': 'Config not found or not owned by you.'}, status=status.HTTP_400_BAD_REQUEST)
            data['config'] = config.id  # Ensure config is valid

        serializer = AssistantSerializer(assistant, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        assistant = self.get_object(id, request.user)
        if assistant is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        assistant.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
