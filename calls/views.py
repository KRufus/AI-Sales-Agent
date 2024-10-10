from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from .models import Call, Log
from assistant.models import Assistant
from .serializers import CallSerializer, LogSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class CallList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        calls = Call.objects.filter(created_by=request.user)
        serializer = CallSerializer(calls, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request):
        data = JSONParser().parse(request)
        serializer = CallSerializer(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CallDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id, user):
        try:
            return Call.objects.get(id=id, created_by=user)
        except Call.DoesNotExist:
            return None

    def get(self, request, id):
        call = self.get_object(id, request.user)
        if call is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CallSerializer(call)
        return JsonResponse(serializer.data)

    def put(self, request, id):
        call = self.get_object(id, request.user)
        if call is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = JSONParser().parse(request)
        serializer = CallSerializer(call, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        call = self.get_object(id, request.user)
        if call is None:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        call.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class LogList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, call_id):
        try:
            call = Call.objects.get(id=call_id, created_by=request.user)
        except Call.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        logs = Log.objects.filter(call=call)
        serializer = LogSerializer(logs, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, call_id):
        try:
            call = Call.objects.get(id=call_id, created_by=request.user)
        except Call.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = JSONParser().parse(request)
        data['call'] = call_id  # Associate the log with the call
        serializer = LogSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Total number of assistants created by the user
        total_assistants = Assistant.objects.filter(created_by=user).count()

        # Total number of calls made by the user
        total_calls = Call.objects.filter(created_by=user).count()

        # Initialize total duration
        total_duration = 0

        # Fetch all calls by the user
        calls = Call.objects.filter(created_by=user)

        for call in calls:
            # Fetch logs for the call ordered by time
            logs = Log.objects.filter(call=call).order_by('time')
            if logs.exists():
                start_time = logs.first().time
                end_time = logs.last().time
                # Calculate duration in seconds
                duration = (end_time - start_time).total_seconds()
                total_duration += duration

        # Calculate average call duration
        average_call_duration = 0
        
        if total_calls > 0:
            average_call_duration = total_duration / total_calls

        # Prepare the response data
        data = {
            'total_assistants': total_assistants,
            'total_calls': total_calls,
            'total_duration_seconds': total_duration,
            'average_call_duration_seconds': average_call_duration,
        }

        return JsonResponse(data, status=200)
