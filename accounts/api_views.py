from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, Company, Attendance, Project
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.forms import MessageForm
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Message
from django.shortcuts import get_object_or_404

from .views import sliding_window_materials

User = get_user_model()


@api_view(['POST'])
def worker_signup_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    company_code = request.data.get('company_code')

    if not username or not password or not company_code:
        return Response({"status": "error", "message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if username is taken
    if CustomUser.objects.filter(username=username).exists():
        return Response({"status": "error", "message": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate company code
    try:
        company = Company.objects.get(code=company_code)
    except Company.DoesNotExist:
        return Response({"status": "error", "message": "Invalid company code"}, status=status.HTTP_400_BAD_REQUEST)

    # Create worker
    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        user_type='worker',
        company=company
    )

    return Response({"status": "success", "message": "Worker account created successfully"})

@csrf_exempt
def worker_login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            user = authenticate(username=username, password=password)
            if user is not None and user.user_type == 'worker':
                token, created = Token.objects.get_or_create(user=user)
                return JsonResponse({
                    'status': 'success',
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'company_id': user.company.id if user.company else None,
                        'company_name': user.company.name if user.company else None
                    }
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'POST request required'}, status=405)

@csrf_exempt
def worker_logout_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token_key = data.get('token')

            if not token_key:
                return JsonResponse({'status': 'error', 'message': 'Token required'}, status=400)

            try:
                token = Token.objects.get(key=token_key)
                token.delete()  # invalidate token
                return JsonResponse({'status': 'success', 'message': 'Logged out successfully'})
            except Token.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'POST request required'}, status=405)

@csrf_exempt
def worker_home_api(request):
    if request.method == 'GET':  # ✅ use GET for fetching data
        # 1. Try to read token from Authorization header
        auth_header = request.headers.get('Authorization')
        token_key = None
        if auth_header and auth_header.startswith("Token "):
            token_key = auth_header.split(" ")[1]

        # 2. Fallback: try query params
        if not token_key:
            token_key = request.GET.get('token')

        if not token_key:
            return JsonResponse({'status': 'error', 'message': 'Token required'}, status=400)

        try:
            token = Token.objects.get(key=token_key)
            user = token.user

            if user.user_type != 'worker':
                return JsonResponse({'status': 'error', 'message': 'User is not a worker'}, status=403)

            now = timezone.now()
            monthly_attendance = Attendance.objects.filter(
                user=user,
                date__year=now.year,
                date__month=now.month
            ).order_by('-date')

            total_days = monthly_attendance.filter(flag=2).count()
            total_hours = monthly_attendance.filter(flag=2).aggregate(
                total=Sum('total_hours')
            )['total'] or 0

            attendance_list = [
                {
                    'date': a.date.strftime('%Y-%m-%d'),
                    'clock_in': a.clock_in.strftime('%H:%M') if a.clock_in else None,
                    'clock_in_latitude': a.clock_in_latitude if hasattr(a, 'clock_in_latitude') else None,
                    'clock_in_longitude': a.clock_in_longitude if hasattr(a, 'clock_in_longitude') else None,
                    'clock_out': a.clock_out.strftime('%H:%M') if a.clock_out else None,
                    'clock_out_latitude': a.clock_out_latitude if hasattr(a, 'clock_out_latitude') else None,
                    'clock_out_longitude': a.clock_out_longitude if hasattr(a, 'clock_out_longitude') else None,
                    'total_hours': a.total_hours,
                    'flag': a.flag,
                }
                for a in monthly_attendance
            ]


            return JsonResponse({
                'status': 'success',
                'total_days': total_days,
                'total_hours': round(total_hours, 2),
                'attendances': attendance_list,
            })

        except Token.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=401)

    return JsonResponse({'status': 'error', 'message': 'GET request required'}, status=405)

@csrf_exempt
def clock_in_api(request):
    if request.method == 'POST':
        token_key = request.POST.get('token') or request.GET.get('token')
        lat = request.POST.get('latitude')
        lon = request.POST.get('longitude')

        if not token_key:
            return JsonResponse({'status': 'error', 'message': 'Token required'}, status=400)

        try:
            token = Token.objects.get(key=token_key)
            user = token.user

            if user.user_type != 'worker':
                return JsonResponse({'status': 'error', 'message': 'User is not a worker'}, status=403)

            today = timezone.now().date()
            last_attendance = Attendance.objects.filter(user=user).order_by('-date').first()

            if last_attendance and last_attendance.date == today and last_attendance.clock_in:
                return JsonResponse({'status': 'error', 'message': 'You have already clocked in today'}, status=400)

            attendance, created = Attendance.objects.get_or_create(user=user, date=today)

            if created or not attendance.clock_in:
                attendance.clock_in = timezone.now()
                attendance.clock_in_latitude = lat if lat else None
                attendance.clock_in_longitude = lon if lon else None
                attendance.flag = 1
                attendance.save()

                return JsonResponse({
                    'status': 'success',
                    'message': f'Clocked in at {attendance.clock_in.strftime("%H:%M:%S")}',
                    'clock_in_time': attendance.clock_in.strftime('%H:%M:%S'),
                    'latitude': attendance.clock_in_latitude,
                    'longitude': attendance.clock_in_longitude
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'You have already clocked in today'}, status=400)

        except Token.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=401)

    return JsonResponse({'status': 'error', 'message': 'POST request required'}, status=405)

def _get_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}

@csrf_exempt
def clock_out_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST request required'}, status=405)

    # Accept token/lat/lon from JSON body or form-data
    data = _get_json(request)
    token_key = data.get('token') or request.POST.get('token') or request.GET.get('token')
    lat = data.get('latitude') or request.POST.get('latitude')
    lon = data.get('longitude') or request.POST.get('longitude')

    if not token_key:
        return JsonResponse({'status': 'error', 'message': 'Token required'}, status=400)

    try:
        token = Token.objects.get(key=token_key)
        user = token.user
    except Token.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=401)

    if getattr(user, 'user_type', None) != 'worker':
        return JsonResponse({'status': 'error', 'message': 'User is not a worker'}, status=403)

    now = timezone.now()
    today = now.date()

    try:
        attendance = Attendance.objects.get(user=user, date=today)
    except Attendance.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'You must clock in before clocking out.'}, status=400)

    if attendance.flag == 1:  # clocked in, not out yet
        attendance.clock_out = now
        attendance.clock_out_latitude = lat if lat else None
        attendance.clock_out_longitude = lon if lon else None

        duration = now - attendance.clock_in
        attendance.total_hours = round(duration.total_seconds() / 3600, 2)
        attendance.flag = 2
        attendance.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Clocked out successfully.',
            'date': str(today),
            'clock_in_time': attendance.clock_in.strftime('%H:%M:%S') if attendance.clock_in else None,
            'clock_out_time': attendance.clock_out.strftime('%H:%M:%S'),
            'clock_out_latitude': attendance.clock_out_latitude,
            'clock_out_longitude': attendance.clock_out_longitude,
            'total_hours': attendance.total_hours,
            'flag': attendance.flag
        })

    elif attendance.flag == 2:
        return JsonResponse({'status': 'error', 'message': 'You have already clocked out today.'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Cannot clock out without clocking in.'}, status=400)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_message_api(request):
    form = MessageForm(request.data, request.FILES)
    if form.is_valid():
        recipient_username = form.cleaned_data['recipient_username']
        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found'}, status=404)

        message = form.save(commit=False)
        message.sender = request.user
        message.recipient = recipient
        message.save()

        return Response({
            'status': 'success',
            'message_id': message.id,
            'sender': message.sender.username,
            'recipient': message.recipient.username,
            'content': message.content,
            'attachment': message.attachment.url if message.attachment else None,
            'timestamp': message.timestamp
        })

    return Response({'status': 'error', 'errors': form.errors}, status=400)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def inbox_api(request):
    # Get all messages where the current user is the recipient
    messages_received = Message.objects.filter(
        recipient=request.user
    ).order_by('-timestamp')

    data = []
    for msg in messages_received:
        data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'recipient': msg.recipient.username,
            'content': msg.content,
            'attachment': msg.attachment.url if msg.attachment else None,
            'timestamp': msg.timestamp
        })

    return Response({'status': 'success', 'messages': data})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reply_message_api(request, message_id):
    # Find the original message
    original = get_object_or_404(Message, id=message_id)

    # Force recipient to be the original sender
    data = request.data.copy()
    data['recipient_username'] = original.sender.username

    form = MessageForm(data, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.sender = request.user
        message.recipient = original.sender
        message.save()

        return Response({
            'status': 'success',
            'message_id': message.id,
            'sender': message.sender.username,
            'recipient': message.recipient.username,
            'content': message.content,
            'attachment': message.attachment.url if message.attachment else None,
            'timestamp': message.timestamp
        })

    return Response({'status': 'error', 'errors': form.errors}, status=400)

@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_message_api(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'status': 'error', 'message': 'Message not found'}, status=404)

    if message.recipient != request.user:
        return Response({'status': 'error', 'message': 'Not authorized to delete this message'}, status=403)

    message.delete()
    return Response({'status': 'success', 'message': 'Message deleted successfully'})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def sent_messages_api(request):
    sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')

    data = []
    for msg in sent_messages:
        data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'recipient': msg.recipient.username,
            'content': msg.content,
            'attachment': msg.attachment.url if msg.attachment else None,
            'timestamp': msg.timestamp
        })

    return Response({'status': 'success', 'sent_messages': data})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def worker_work_page_api(request):
    user = request.user
    if user.user_type != 'worker':
        return Response({'status': 'error', 'message': 'You are not allowed here'}, status=403)

    # All assigned aluminum projects
    projects = user.assigned_projects.filter(project_type='aluminum').values(
        'id', 'project_number', 'address'  # CORRECT field name
    )

    # If project_id is given, get materials for that project
    project_id = request.GET.get('project_id')
    selected_project = None
    aluminum_data = None

    if project_id:
        selected_project = get_object_or_404(Project, id=project_id, workers=user)
        aluminum_data = sliding_window_materials(project_id)

    return Response({
        'status': 'success',
        'projects': list(projects),
        'selected_project': selected_project.id if selected_project else None,
        'aluminum_data': aluminum_data
    })