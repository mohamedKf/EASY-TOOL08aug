import traceback
import uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter
from collections import defaultdict
from django.db import models, transaction
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm  # Add to your existing cm import
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from .forms import ScrewForm, ProfileSetForm, MetalProfileForm, DrywallBoardForm, OrderStatusUpdateForm, \
    DeliveryDateForm
from .models import Screw, ProfileSet, MetalProfile, DrywallBoard, Order, OrderItem, \
    generate_monthly_reports_from_attendance, PasswordResetCode, DrywallMaterial
import math
import os
from math import ceil
from decimal import Decimal, ROUND_UP
from django.utils.timezone import now
from django.http import HttpResponse, HttpResponseForbidden, FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
import random
from datetime import datetime
from .forms import MessageForm, AluminumPriceForm, GlassPriceForm, CreateCompanyForm, RoomForm, \
    AluminumItemForm, DrywallBoardPriceForm, MetalProfilePriceForm
from .models import Message, CustomUser, AluminumPrice, GlassPrice, Room, Ceiling, Wall, \
    DrywallBoardPrice, MetalProfilePrice
from .forms import SignUpForm, LoginForm
from .models import CustomUser, Attendance
from django.contrib.auth import get_user_model
from .models import MonthlyReport
from django.contrib.auth.decorators import login_required
from .forms import ProjectForm
from .models import Project, CustomUser
from django.shortcuts import render, get_object_or_404
from .models import Project
from django.shortcuts import get_object_or_404, redirect
from .models import Window, WindowSash, Glass
from django.forms import modelformset_factory
from .models import Project, Glass, Window, WindowFrame, WindowSash, Door, DoorFrame, DoorSash,Company
from django.shortcuts import render, redirect
from .forms import SignUpForm
from .models import Company
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Glass
from .forms import (
    WindowForm, WindowFrameForm, WindowSashForm,
    DoorForm, DoorFrameForm, DoorSashForm, GlassForm
)
from django.contrib.auth.hashers import make_password
from datetime import date
import calendar
from django.db.models import Sum
from .forms import PayrollUploadForm
from django.contrib.auth.models import User
from django.forms import formset_factory, modelformset_factory
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.conf import settings
from django.forms import modelformset_factory
from twilio.rest import Client



RoomFormSet = modelformset_factory(Room, form=RoomForm, extra=1)
AluminumItemFormSet = formset_factory(AluminumItemForm, extra=1)



User = get_user_model()



def create_contractor_files(username):
    # 👇 This will create: easy_tool/contractors/<username>/
    base_path = os.path.join(settings.BASE_DIR, 'contractors', username)

    os.makedirs(base_path, exist_ok=True)

    subfolders = ['workers_log', 'projects', 'materials']
    for folder_name in subfolders:
        folder_path = os.path.join(base_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)


def signup_view(request):
    if request.method == 'POST':
        print("🔹 Signup POST received:", request.POST)  # DEBUG

        form = SignUpForm(request.POST)
        company_code = request.POST.get('company_code')
        print("🔹 Company code received:", company_code)  # DEBUG

        if form.is_valid():
            user = form.save(commit=False)
            print("✅ Form valid. User (before save):", user)  # DEBUG

            user.set_password(form.cleaned_data['password'])
            print("🔹 Password hashed.")  # DEBUG

            if user.user_type == 'worker':
                try:
                    company = Company.objects.get(code=company_code)
                    user.company = company
                    print(f"✅ Worker linked to company: {company.name}")  # DEBUG
                except Company.DoesNotExist:
                    print("❌ Invalid company code!")  # DEBUG
                    return render(request, 'accounts/signup.html', {
                        'form': form,
                        'error': 'Invalid company code. Please check and try again.'
                    })

            user.save()
            print(f"✅ User {user.username} saved to DB.")  # DEBUG

            if user.user_type == 'contractor':
                create_contractor_files(user.username)
                print(f"📂 Contractor files created for {user.username}")  # DEBUG

            return redirect('login')
        else:
            print("❌ Signup form invalid:", form.errors)  # DEBUG

    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        print("🔹 Login POST received:", request.POST)  # DEBUG

        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            print(f"🔹 Attempting login for user: {username}")  # DEBUG

            user = authenticate(request, username=username, password=password)
            if user is not None:
                print(f"✅ Authenticated user: {user.username}, type: {user.user_type}")  # DEBUG
                login(request, user)

                if user.user_type == 'contractor' and user.company_id:
                    print(f"📊 Generating monthly reports for company {user.company_id}")  # DEBUG
                    generate_monthly_reports_from_attendance(user.company_id)

                if user.is_staff:
                    print("➡ Redirecting to admin dashboard")  # DEBUG
                    return redirect('admin_company_list')
                elif user.user_type == 'worker':
                    print("➡ Redirecting to worker page")  # DEBUG
                    return redirect('worker_page')
                elif user.user_type == 'contractor':
                    print("➡ Redirecting to contractor page")  # DEBUG
                    return redirect('contractor_page')
                elif user.user_type == 'supplier':
                    print("➡ Redirecting to supplier home")  # DEBUG
                    return redirect('supplier_home')
            else:
                print("❌ Authentication failed for:", username)  # DEBUG
                form.add_error(None, 'Invalid username or password')
        else:
            print("❌ Login form invalid:", form.errors)  # DEBUG
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    print(f"🔹 User {request.user} logging out...")  # DEBUG
    logout(request)
    print("✅ Logout successful.")  # DEBUG
    return redirect('login')




def reset_password(request):
    step = "phone"  # default: ask for username + phone

    if request.method == "POST":
        # Step 1: username + phone → send code
        if "phone" in request.POST:
            phone = request.POST.get("phone", "").strip()
            username = request.POST.get("username", "").strip()

            try:
                user = CustomUser.objects.get(username=username, phone=phone)
                code = str(random.randint(100000, 999999))

                # Save reset code
                reset_entry = PasswordResetCode.objects.create(user=user, code=code)
                print(f"[DEBUG] Created reset code {reset_entry.code} for user {username} at {reset_entry.created_at}")

                try:
                    # Send code via Twilio WhatsApp
                    client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)
                    client.messages.create(
                        from_=settings.TWILIO_WHATSAPP_FROM,
                        body=f"Your reset code is {code}. Valid for 10 minutes.",
                        to=f"whatsapp:{phone}"
                    )
                    messages.success(request, "Verification code sent to your WhatsApp.")
                except Exception as e:
                    # Fallback for development/testing without Twilio
                    print(f"[DEBUG] Twilio error: {e}. Code for {username} ({phone}) = {code}")
                    messages.warning(request, "Twilio not configured. Code printed in console.")

                step = "verify"

            except CustomUser.DoesNotExist:
                messages.error(request, "Invalid username or phone number.")

        # Step 2: verify code + reset password
        elif "code" in request.POST:
            code = request.POST.get("code", "").strip()
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            print(f"[DEBUG] User entered code: {code}")

            try:
                # Get the latest unused code
                reset = PasswordResetCode.objects.filter(code=code, is_used=False).latest("created_at")
                print(f"[DEBUG] Found code in DB: {reset.code}, created at {reset.created_at}, used={reset.is_used}")

                # Check expiry
                age_seconds = (timezone.now() - reset.created_at).total_seconds()
                print(f"[DEBUG] Code age: {age_seconds:.1f} seconds")

                if not reset.is_used and age_seconds < 600:  # valid for 10 mins
                    if new_password == confirm_password:
                        reset.user.password = make_password(new_password)
                        reset.user.save()
                        reset.is_used = True
                        reset.save()
                        messages.success(request, "Password updated successfully. You can now log in.")
                        print(f"[DEBUG] Password updated for user {reset.user.username}")
                        return redirect("login")
                    else:
                        messages.error(request, "Passwords do not match.")
                        print("[DEBUG] Passwords did not match")
                else:
                    messages.error(request, "Code expired or already used.")
                    print("[DEBUG] Code expired or already used")
            except PasswordResetCode.DoesNotExist:
                messages.error(request, "Invalid code.")
                print("[DEBUG] No matching reset code found")
            step = "verify"

    return render(request, "accounts/reset_password.html", {"step": step})


def home_page(request):
    return render(request, 'home.html')

@login_required
def worker_page(request):
    user = request.user
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Filter attendance for the current month
    monthly_attendance = Attendance.objects.filter(
        user=user,
        date__year=current_year,
        date__month=current_month
    ).order_by('-date')

    # Count only fully completed days (flag = 2)
    total_days = monthly_attendance.filter(flag=2).count()

    # Sum total_hours for all completed days
    total_hours = monthly_attendance.filter(flag=2).aggregate(
        total=models.Sum('total_hours')
    )['total'] or 0

    context = {
        'attendances': monthly_attendance,
        'total_days': total_days,
        'total_hours': round(total_hours, 2),
        'now': now
    }
    return render(request, 'accounts/worker.html', context)

@login_required
def update_worker_wage(request, worker_id):
    if request.method == 'POST' and request.user.user_type == 'contractor':
        worker = get_object_or_404(CustomUser, id=worker_id, user_type='worker', company=request.user.company)
        try:
            new_wage = float(request.POST.get('hourly_wage'))
            worker.hourly_wage = new_wage
            worker.save()
        except (ValueError, TypeError):
            pass  # Optional: handle invalid input
    return redirect('contractor_worker_log')

@login_required
def contractor_page(request):
    if request.user.user_type != 'contractor':
        return redirect('home')

    # Check if contractor's folder exists inside easy_tool/contractors/
    contractor_folder = os.path.join(settings.BASE_DIR, 'contractors', request.user.username)
    if not os.path.exists(contractor_folder):
        create_contractor_files(request.user.username)

    projects = Project.objects.filter(contractor=request.user)
    return render(request, 'accounts/contractor.html', {'projects': projects})


@login_required
def create_company_view(request):
    def generate_company_code():
        while True:
            code = str(random.randint(10000, 99999))
            if not Company.objects.filter(code=code).exists():
                return code

    user = request.user

    if user.user_type != 'contractor':
        return render(request, 'accounts/create_company.html', {
            'error': 'Only contractors can create companies.'
        })

    if user.company:
        return render(request, 'accounts/create_company.html', {
            'error': 'You are already part of a company.'
        })

    if request.method == 'POST':
        form = CreateCompanyForm(request.POST, user=user)
        if form.is_valid():
            company = form.save(commit=False)
            company.contractor = user
            company.code = generate_company_code()  # now works
            company.save()

            user.company = company
            user.save()
            login(request, user)
            return redirect('pricing')
        else:
            print("❗ FORM ERRORS:", form.errors)
            print("❗ NON-FIELD ERRORS:", form.non_field_errors())

        return render(request, 'accounts/create_company.html', {'form': form})

    else:
        form = CreateCompanyForm(user=user)
        return render(request, 'accounts/create_company.html', {'form': form})


@login_required
def clock_in_view(request):
    user = request.user
    today = timezone.now().date()  # Get today's date

    # Get coordinates from request (later from app or form)
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')

    last_attendance = Attendance.objects.filter(user=user).order_by('-date').first()

    if last_attendance and last_attendance.date == today and last_attendance.clock_in:
        messages.warning(request, "⚠️ You have already clocked in today.")
    else:
        attendance, created = Attendance.objects.get_or_create(user=user, date=today)

        if created or not attendance.clock_in:
            attendance.clock_in = timezone.now()
            attendance.clock_in_latitude = lat if lat else None
            attendance.clock_in_longitude = lon if lon else None
            attendance.flag = 1
            attendance.save()

            messages.success(request, f"✅ Clocked in at {attendance.clock_in.strftime('%H:%M:%S')}")
        else:
            messages.warning(request, "⚠️ You have already clocked in today.")

    return redirect('worker_page')


@login_required
def clock_out_view(request):
    user = request.user
    now = timezone.now()
    today = now.date()

    # Get coordinates from request
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')

    try:
        attendance = Attendance.objects.get(user=user, date=today)
    except Attendance.DoesNotExist:
        messages.error(request, "⚠️ You must clock in before clocking out.")
        return redirect('worker_page')

    if attendance.flag == 1:
        attendance.clock_out = now
        attendance.clock_out_latitude = lat if lat else None
        attendance.clock_out_longitude = lon if lon else None

        duration = now - attendance.clock_in
        attendance.total_hours = round(duration.total_seconds() / 3600, 2)
        attendance.flag = 2
        attendance.save()

        messages.success(request, f"✅ Clocked out at {now.strftime('%H:%M:%S')} on {now.strftime('%d/%m/%Y')}. Total worked: {attendance.total_hours:.2f} hours.")
    elif attendance.flag == 2:
        messages.warning(request, "⚠️ You have already clocked out today.")
    else:
        messages.error(request, "⚠️ Cannot clock out without clocking in.")

    return redirect('worker_page')


def send_message_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = MessageForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('inbox')
    else:
        form = MessageForm(user=request.user)

    return render(request, 'accounts/send_message.html', {'form': form})

def inbox_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    messages_received = Message.objects.filter(recipient=request.user).order_by('-timestamp')

    return render(request, 'accounts/inbox.html', {
        'messages_received': messages_received
    })
@login_required
def clock_in_view(request):
    user = request.user
    today = timezone.now().date()  # Get today's date

    # Get coordinates from request (later from app or form)
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')

    last_attendance = Attendance.objects.filter(user=user).order_by('-date').first()

    if last_attendance and last_attendance.date == today and last_attendance.clock_in:
        messages.warning(request, "⚠️ You have already clocked in today.")
    else:
        attendance, created = Attendance.objects.get_or_create(user=user, date=today)

        if created or not attendance.clock_in:
            attendance.clock_in = timezone.now()
            attendance.clock_in_latitude = lat if lat else None
            attendance.clock_in_longitude = lon if lon else None
            attendance.flag = 1
            attendance.save()

            messages.success(request, f"✅ Clocked in at {attendance.clock_in.strftime('%H:%M:%S')}")
        else:
            messages.warning(request, "⚠️ You have already clocked in today.")

    return redirect('worker_page')
def reply_message_view(request, message_id):
    original = Message.objects.get(id=message_id)
    form = MessageForm(initial={'recipient_username': original.sender.username})
    return render(request, 'accounts/send_message.html', {
        'form': form,
        'reply_to': original.sender.username
    })


def delete_message_view(request, message_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        message = get_object_or_404(Message, id=message_id, recipient=request.user)
        if request.method == 'POST':
            message.delete()
            messages.success(request, "Message deleted successfully.")
        else:
            messages.error(request, "Invalid request method.")
    except Message.DoesNotExist:
        messages.error(request, "Message not found or you are not authorized to delete this message.")

    return redirect('inbox')


@login_required
def sent_messages_view(request):
    sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'accounts/sent_messages.html', {'sent_messages': sent_messages})

@login_required
def create_project_view(request):
    user = request.user
    if user.user_type != 'contractor':
        return redirect('home')

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, contractor=user)
        if form.is_valid():
            project = form.save(commit=False)
            project.contractor = user
            project.save()
            form.save_m2m()  # Save many-to-many (workers)
            return redirect('project_detail', project_id=project.pk)

    else:
        form = ProjectForm(contractor=user)

    return render(request, 'accounts/create_project.html', {'form': form})


@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if project.project_type == 'aluminum':
        return redirect('add_aluminum_item', project_id=project.id)
    elif project.project_type == 'drywall':
        return redirect('add_drywall_room', project_id=project.id)
    else:
        return HttpResponse("Unknown project type", status=400)


@login_required
def add_room(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save(commit=False)
            room.project = project
            room.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = RoomForm()

    return render(request, 'accounts/add_room.html', {'form': form, 'project': project})


@login_required
def add_rooms_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        room_count = int(request.POST.get('room_count', 0))

        for i in range(room_count):
            room_name = request.POST.get(f'room_name_{i}')
            if room_name:
                room = Room.objects.create(name=room_name, project=project)

                # Count how many items (windows/doors) were added in this room
                item_count = int(request.POST.get(f'item_count_{i}', 0))

                for j in range(item_count):
                    item_type = request.POST.get(f'item_type_{i}_{j}')
                    subtype = request.POST.get(f'subtype_{i}_{j}')
                    aluminum_type = request.POST.get(f'aluminum_type_{i}_{j}')
                    height_l = request.POST.get(f'height_left_{i}_{j}', 0)
                    height_m = request.POST.get(f'height_middle_{i}_{j}', 0)
                    height_r = request.POST.get(f'height_right_{i}_{j}', 0)
                    width_t = request.POST.get(f'width_top_{i}_{j}', 0)
                    width_m = request.POST.get(f'width_middle_{i}_{j}', 0)
                    width_b = request.POST.get(f'width_bottom_{i}_{j}', 0)
                    glass_type = request.POST.get(f'glass_type_{i}_{j}')

                    if item_type == 'window':
                        Window.objects.create(
                            room=room,
                            subtype=subtype,
                            aluminum_type=aluminum_type,
                            height_left=height_l,
                            height_middle=height_m,
                            height_right=height_r,
                            width_top=width_t,
                            width_middle=width_m,
                            width_bottom=width_b,
                            glass_type=glass_type
                        )
                    elif item_type == 'door':
                        Door.objects.create(
                            room=room,
                            subtype=subtype,
                            aluminum_type=aluminum_type,
                            height_left=height_l,
                            height_middle=height_m,
                            height_right=height_r,
                            width_top=width_t,
                            width_middle=width_m,
                            width_bottom=width_b,
                            glass_type=glass_type
                        )

        return redirect('project_detail', project_id=project.id)

    return render(request, 'accounts/aluminum_add_item.html', {'project': project})





@login_required
def pricing_view(request):
    contractor = request.user
    company = contractor.company

    if not company:
        return render(request, 'accounts/pricing.html', {
            'error': 'You must create or join a company before setting prices.'
        })

    # Ensure defaults exist for aluminum and glass types
    aluminum_types = ['1700', '7000', '7300', '9000', '2200', '9400', '9200', '2000', '4500', '4400', '4300']
    glass_types = ['transparent', 'anti_sun', 'shadowed', 'בודדי']
    board_colors = ['green', 'blue', 'white', 'pink']
    board_sizes = ['200x120', '260x120', '300x120']

    for atype in aluminum_types:
        AluminumPrice.objects.get_or_create(
            contractor=contractor, company=company, aluminum_type=atype,
            defaults={'price_per_m2': 0}
        )

    for gtype in glass_types:
        GlassPrice.objects.get_or_create(
            contractor=contractor, company=company, glass_type=gtype,
            defaults={'price_per_m2': 0}
        )

    for c in board_colors:
        for s in board_sizes:
            DrywallBoardPrice.objects.get_or_create(
                contractor=contractor, company=company, color=c, size=s,
                defaults={'price_per_board': 0}
            )

    # Query all pricing objects
    aluminum_prices = AluminumPrice.objects.filter(contractor=contractor, company=company)
    glass_prices = GlassPrice.objects.filter(contractor=contractor, company=company)
    metal_prices = MetalProfilePrice.objects.filter(contractor=contractor, company=company)
    board_prices = DrywallBoardPrice.objects.filter(contractor=contractor, company=company)

    # Create formsets
    AluminumFormSet = modelformset_factory(AluminumPrice, form=AluminumPriceForm, extra=0)
    GlassFormSet = modelformset_factory(GlassPrice, form=GlassPriceForm, extra=0)
    MetalFormSet = modelformset_factory(MetalProfilePrice, form=MetalProfilePriceForm, extra=0)
    BoardFormSet = modelformset_factory(DrywallBoardPrice, form=DrywallBoardPriceForm, extra=0)

    if request.method == 'POST':
        aluminum_formset = AluminumFormSet(request.POST, queryset=aluminum_prices, prefix='aluminum')
        glass_formset = GlassFormSet(request.POST, queryset=glass_prices, prefix='glass')
        metal_formset = MetalFormSet(request.POST, queryset=metal_prices, prefix='metal')
        board_formset = BoardFormSet(request.POST, queryset=board_prices, prefix='board')

        print("🔩 Aluminum formset valid?", aluminum_formset.is_valid())
        print("🪟 Glass formset valid?", glass_formset.is_valid())
        print("🧱 Metal Profile formset valid?", metal_formset.is_valid())
        print("🧱 Board formset valid?", board_formset.is_valid())
        if not metal_formset.is_valid():
            print("❌ Metal formset errors:")
            for form in metal_formset:
                print(form.errors)

        if not board_formset.is_valid():
            print("❌ Board formset errors:")
            for form in board_formset:
                print(form.errors)

        if aluminum_formset.is_valid():
            for form in aluminum_formset.save(commit=False):
                form.contractor = contractor
                form.company = company
                form.save()

        if glass_formset.is_valid():
            for form in glass_formset.save(commit=False):
                form.contractor = contractor
                form.company = company
                form.save()

        if metal_formset.is_valid():
            for form in metal_formset.save(commit=False):
                form.contractor = contractor
                form.company = company
                form.save()

        if board_formset.is_valid():
            for form in board_formset.save(commit=False):
                form.contractor = contractor
                form.company = company
                form.save()

        return redirect('pricing')

    else:
        aluminum_formset = AluminumFormSet(queryset=aluminum_prices, prefix='aluminum')
        glass_formset = GlassFormSet(queryset=glass_prices, prefix='glass')
        metal_formset = MetalFormSet(queryset=metal_prices, prefix='metal')
        board_formset = BoardFormSet(queryset=board_prices, prefix='board')

    return render(request, 'accounts/pricing.html', {
        'aluminum_formset': aluminum_formset,
        'glass_formset': glass_formset,
        'metal_formset': metal_formset,
        'board_formset': board_formset,
    })


@login_required
def my_reports_view(request):
    reports = MonthlyReport.objects.filter(worker=request.user).order_by('-year', 'month')

    reports_by_year = defaultdict(list)

    for report in reports:
        reports_by_year[report.year].append({
            'month_name': calendar.month_name[report.month],
            'total_days': report.total_days,
            'total_hours': report.total_hours,
            'payroll_file': report.payroll_file,
        })

    return render(request, 'accounts/my_reports.html', {
        'reports_by_year': dict(reports_by_year)
    })

@login_required
def contractor_worker_log_view(request):
    if request.user.user_type != 'contractor':
        return redirect('home')

    # Get all workers that belong to the contractor's company
    workers = CustomUser.objects.filter(user_type='worker', company_id=request.user.company_id)

    reports_by_worker = {}

    for worker in workers:
        reports = MonthlyReport.objects.filter(worker=worker).order_by('-year', '-month')
        worker_reports = []

        for report in reports:
            attendance_records = Attendance.objects.filter(
                user=worker,
                date__year=report.year,
                date__month=report.month
            ).order_by('date')

            worker_reports.append({
                'report': report,
                'attendance': attendance_records,
                'month_name': calendar.month_name[report.month],

            })

        reports_by_worker[worker] = worker_reports

    # Handle payroll file upload
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        report = get_object_or_404(MonthlyReport, id=report_id)
        form = PayrollUploadForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            return redirect('contractor_worker_log')

    return render(request, 'accounts/contractor_worker_log.html', {
        'reports_by_worker': reports_by_worker,
        'form': PayrollUploadForm(),
    })


@login_required
def worker_company_view(request):
    user = request.user

    if user.user_type != 'worker':
        return redirect('home')

    if request.method == 'POST':
        if 'leave_company' in request.POST:
            if user.company:
                user.company.workers.remove(user)
            user.company = None
            user.save()
            return redirect('worker_company')

        elif 'join_company' in request.POST:
            code = request.POST.get('company_code')
            try:
                company = Company.objects.get(code=code)
                user.company = company
                user.save()

                
                company.workers.add(user)

                return redirect('worker_company')
            except Company.DoesNotExist:
                return render(request, 'accounts/worker_company.html', {
                    'error': 'Invalid company code.',
                })

    return render(request, 'accounts/worker_company.html', {
        'company': user.company
    })

@login_required
def contractor_company_view(request):
    if request.user.user_type != 'contractor':
        return redirect('home')

    try:
        company = request.user.owned_company
    except Company.DoesNotExist:
        company = None

    if request.method == 'POST':
        if 'create_company' in request.POST:
            name = request.POST.get('name')
            password = request.POST.get('password')

            # Verify contractor's password
            user = authenticate(username=request.user.username, password=password)
            if user is None:
                messages.error(request, "❌ Incorrect password.")
            else:
                # Generate unique 5-digit code
                while True:
                    code = str(random.randint(10000, 99999))
                    if not Company.objects.filter(code=code).exists():
                        break

                Company.objects.create(
                    name=name,
                    code=code,
                    contractor=request.user
                )
                return redirect('contractor_company')

        elif 'delete_company' in request.POST and company:
            company.delete()
            return redirect('contractor_company')

    return render(request, 'accounts/contractor_company.html', {
        'company': company
    })

@login_required
def add_aluminum_item(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Constants per aluminum type
    ALUMINUM_CONSTANTS = {
        # --- Sliding windows ---
        "1700": {"GIRTH": 1.5, "DEPTH": 2,   "FRAME_INSIDE": 1,   "PROFILE_WIDTH": 1.2},
        "7000": {"GIRTH": 2.0, "DEPTH": 2.5, "FRAME_INSIDE": 1.2, "PROFILE_WIDTH": 1.5},
        "7300": {"GIRTH": 2.2, "DEPTH": 3,   "FRAME_INSIDE": 1.3, "PROFILE_WIDTH": 1.6},
        "9000": {"GIRTH": 2.5, "DEPTH": 3.2, "FRAME_INSIDE": 1.4, "PROFILE_WIDTH": 1.8},
        "9200": {"GIRTH": 2.7, "DEPTH": 3.5, "FRAME_INSIDE": 1.5, "PROFILE_WIDTH": 2.0},

        # --- Multi-bolt windows ---
        "4400": {"GIRTH": 1.8, "DEPTH": 2.2, "FRAME_INSIDE": 1.1, "PROFILE_WIDTH": 1.3},
        "4300": {"GIRTH": 1.9, "DEPTH": 2.3, "FRAME_INSIDE": 1.1, "PROFILE_WIDTH": 1.3},
        "4500": {"GIRTH": 2.0, "DEPTH": 2.4, "FRAME_INSIDE": 1.2, "PROFILE_WIDTH": 1.4},
        "9400": {"GIRTH": 2.3, "DEPTH": 2.8, "FRAME_INSIDE": 1.3, "PROFILE_WIDTH": 1.5},

        # --- Sliding doors ---
        "2200": {"GIRTH": 2.0, "DEPTH": 2.5, "FRAME_INSIDE": 1.2, "PROFILE_WIDTH": 1.5},
        # Reuses 7300, 9200, 9400 (already defined above) for sliding doors too

        # --- Multi-bolt doors ---
        "2000": {"GIRTH": 1.7, "DEPTH": 2.0, "FRAME_INSIDE": 1.0, "PROFILE_WIDTH": 1.2},
        # Reuses 4500, 4400 (already defined above) for multi-bolt doors too
    }

    if request.method == 'POST':
        room_count = int(request.POST.get("room_count", 0))

        for i in range(room_count):
            room_name = request.POST.get(f"room_name_{i}", f"Room {i}")
            room_file = request.FILES.get(f"room_file_{i}")

            # Create Room
            room = Room.objects.create(
                name=room_name,
                project=project,
                blueprint=room_file
            )

            item_count = int(request.POST.get(f'item_count_{i}', 0))

            for j in range(item_count):
                try:
                    prefix = f'{i}_{j}'
                    item_type = request.POST.get(f'item_type_{prefix}')
                    subtype = request.POST.get(f'subtype_{prefix}')
                    aluminum_type = request.POST.get(f'aluminum_type_{prefix}')
                    glass_type = request.POST.get(f'glass_type_{prefix}')
                    sash_count = int(request.POST.get(f'number_of_sashs_{prefix}', 2))

                    # Load constants for this aluminum type
                    constants = ALUMINUM_CONSTANTS.get(
                        aluminum_type,
                        {"GIRTH": 1, "DEPTH": 1, "FRAME_INSIDE": 1, "PROFILE_WIDTH": 1}
                    )
                    GIRTH = constants["GIRTH"]
                    DEPTH = constants["DEPTH"]
                    FRAME_INSIDE = constants["FRAME_INSIDE"]
                    PROFILE_WIDTH = constants["PROFILE_WIDTH"]

                    height_values = [
                        float(request.POST.get(f'height_left_{prefix}', 0)),
                        float(request.POST.get(f'height_middle_{prefix}', 0)),
                        float(request.POST.get(f'height_right_{prefix}', 0)),
                    ]
                    width_values = [
                        float(request.POST.get(f'width_top_{prefix}', 0)),
                        float(request.POST.get(f'width_middle_{prefix}', 0)),
                        float(request.POST.get(f'width_bottom_{prefix}', 0)),
                    ]

                    min_height = min(height_values) if height_values else 0
                    min_width = min(width_values) if width_values else 0

                    if item_type == 'window':
                        window_number = f"W-{project.id}-{room.id}-{j}"

                        frame_side = min_height - 1
                        frame_top = min_width - 1
                        frame_bottom = min_width - 1

                        sash_side = min_height - FRAME_INSIDE
                        sash_top_bottom = (min_width - ((sash_count - 1) * GIRTH)) / sash_count
                        glass_width = sash_top_bottom - DEPTH - 1
                        glass_height = sash_side - DEPTH - 1

                        window = Window.objects.create(
                            room=room,
                            project=project,
                            window_type=subtype,
                            aluminum_type=aluminum_type,
                            number_of_sashs=sash_count,
                            window_number=window_number
                        )

                        WindowFrame.objects.create(
                            window=window,
                            side=frame_side,
                            top=frame_top,
                            bottom=frame_bottom
                        )

                        for _ in range(sash_count):
                            glass = Glass.objects.create(
                                glass_type=glass_type,
                                height=glass_height,
                                width=glass_width
                            )
                            WindowSash.objects.create(
                                window=window,
                                side=sash_side,
                                top=sash_top_bottom,
                                bottom=sash_top_bottom,
                                glass=glass
                            )

                    elif item_type == 'door':
                        door_number = f"D-{project.id}-{room.id}-{j}"

                        door = Door.objects.create(
                            room=room,
                            project=project,
                            door_type=subtype,
                            aluminum_type=aluminum_type,
                            number_of_sashs=sash_count,
                            door_number=door_number
                        )

                        frame_side = min_height - 1
                        frame_top = min_width - 1
                        frame_bottom = frame_top if subtype == 'sliding' else None

                        DoorFrame.objects.create(
                            door=door,
                            side=frame_side,
                            top=frame_top,
                            bottom=frame_bottom
                        )

                        if subtype == 'multi_bolt':
                            sash_side = min_height - 1 - PROFILE_WIDTH
                            sash_top_bottom = (min_width - 1 - (2 * PROFILE_WIDTH)) / sash_count
                        else:  # sliding
                            sash_side = min_height - FRAME_INSIDE
                            sash_top_bottom = (min_width - ((sash_count - 1) * GIRTH)) / sash_count

                        glass_width = sash_top_bottom - DEPTH - 1
                        glass_height = sash_side - DEPTH - 1

                        for _ in range(sash_count):
                            glass = Glass.objects.create(
                                glass_type=glass_type,
                                height=glass_height,
                                width=glass_width
                            )
                            DoorSash.objects.create(
                                door=door,
                                side=sash_side,
                                top=sash_top_bottom,
                                bottom=sash_top_bottom,
                                glass=glass
                            )

                except Exception as e:
                    print(f"❌ Error in Room '{room.name}', Item {j}: {e}")
                    traceback.print_exc()
                    continue

        return redirect('project_detail', project_id=project.id)

    return render(request, 'accounts/aluminum_add_item.html', {
        'project': project,
    })


def parse_aluminum_form_data(post_data):
    room_data = []
    room_count = int(post_data.get("room_count", 0))

    for i in range(room_count):
        room = {
            "name": post_data.get(f"room_name_{i}", f"Room {i}"),
            "file": post_data.get(f"room_file_{i}", None),
            "items": []
        }

        item_count = int(post_data.get(f"item_count_{i}", 0))
        for j in range(item_count):
            prefix = f"{i}_{j}"
            item = {
                "type": post_data.get(f"item_type_{prefix}"),
                "subtype": post_data.get(f"subtype_{prefix}"),
                "aluminum_type": post_data.get(f"aluminum_type_{prefix}"),
                "glass_type": post_data.get(f"glass_type_{prefix}"),
                "heights": [
                    float(post_data.get(f"height_left_{prefix}", 0)),
                    float(post_data.get(f"height_middle_{prefix}", 0)),
                    float(post_data.get(f"height_right_{prefix}", 0)),
                ],
                "widths": [
                    float(post_data.get(f"width_top_{prefix}", 0)),
                    float(post_data.get(f"width_middle_{prefix}", 0)),
                    float(post_data.get(f"width_bottom_{prefix}", 0)),
                ],
            }
            room["items"].append(item)

        room_data.append(room)

    return room_data

@login_required
def project_list_view(request):
    selected_project = None
    rooms = []
    project_id = request.GET.get('project_id')

    if project_id:
        selected_project = get_object_or_404(Project, id=project_id, contractor=request.user)
        rooms = selected_project.rooms.prefetch_related('windows', 'doors', 'walls', 'ceilings')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_room':
            room_id = request.POST.get('room_id')
            Room.objects.filter(id=room_id, project__contractor=request.user).delete()

        elif action == 'delete_item':
            item_type = request.POST.get('item_type')
            item_id = request.POST.get('item_id')

            if item_type == 'window':
                Window.objects.filter(id=item_id, project__contractor=request.user).delete()
            elif item_type == 'door':
                Door.objects.filter(id=item_id, project__contractor=request.user).delete()
            elif item_type == 'wall':
                Wall.objects.filter(id=item_id, room__project__contractor=request.user).delete()
            elif item_type == 'ceiling':
                Ceiling.objects.filter(id=item_id, room__project__contractor=request.user).delete()

        return redirect(f"{request.path}?project_id={project_id}")

    projects = Project.objects.filter(contractor=request.user)

    return render(request, 'accounts/project_list.html', {
        'projects': projects,
        'selected_project': selected_project,
        'rooms': rooms
    })


def create_window_sashes(request, window_id):
    window = get_object_or_404(Window, id=window_id)
    frame = window.window_frame
    sash_count = window.number_of_sashs

    # Define configuration variables inside the function
    GIRTH = 1          # Profile width of sash (temporary, adjustable later)
    DEPTH = 1          # Depth of profile (how much space glass frame takes inside)
    FRAME_INSIDE = 1   # Inner spacing of frame between top and bottom

    frame_width = frame.top  # Assuming top = bottom frame
    sash_top_bottom = (frame_width / (sash_count - 1)) * GIRTH
    sash_side = frame.side - FRAME_INSIDE

    for i in range(sash_count):
        glass_width = sash_top_bottom - DEPTH - 1
        glass_height = sash_side - DEPTH - 1
        glass_area = glass_width * glass_height  # Optional, for logging/debug

        glass = Glass.objects.create(
            glass_type='transparent',  # Replace with real type later
            height=glass_height,
            width=glass_width
        )

        WindowSash.objects.create(
            window=window,
            side=sash_side,
            top=sash_top_bottom,
            bottom=sash_top_bottom,
            glass=glass
        )

    return redirect('project_detail', project_id=window.project.id)

@login_required
def add_drywall_room(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # 🔒 Redirect if project is not of type 'drywall'
    if project.project_type != 'drywall':
        return redirect('project_detail', project_id=project.id)

    rooms = Room.objects.filter(project=project).prefetch_related('walls', 'ceilings')

    if request.method == 'POST':
        room_count = int(request.POST.get('room_count', 0))

        for i in range(room_count):
            room_name = request.POST.get(f'room_name_{i}')
            blueprint = request.FILES.get(f'room_file_{i}')

            if not room_name:
                continue

            room = Room.objects.create(
                name=room_name,
                project=project,
                blueprint=blueprint
            )

            # 🔧 Add Walls
            wall_count = int(request.POST.get(f'wall_count_{i}', 0))
            for j in range(wall_count):
                Wall.objects.create(
                    room=room,
                    width=request.POST.get(f'wall_width_{i}_{j}', 0),
                    height=request.POST.get(f'wall_height_{i}_{j}', 0),
                    drywall_type=request.POST.get(f'wall_type_{i}_{j}', ''),
                    stud_thickness=request.POST.get(f'wall_stud_{i}_{j}', ''),
                    number_of_layers=int(request.POST.get(f'wall_layers_{i}_{j}', 1)),
                    double_sided=bool(request.POST.get(f'wall_double_{i}_{j}'))
                )

            # 🔧 Add Ceilings
            ceiling_count = int(request.POST.get(f'ceiling_count_{i}', 0))
            for j in range(ceiling_count):
                Ceiling.objects.create(
                    room=room,
                    area=request.POST.get(f'ceiling_area_{i}_{j}', 0),
                    drywall_type=request.POST.get(f'ceiling_type_{i}_{j}', ''),
                    stud_thickness=request.POST.get(f'ceiling_stud_{i}_{j}', ''),
                    board_length=request.POST.get(f'ceiling_board_length_{i}_{j}', 2.6)
                )

        return redirect('project_detail', project_id=project.id)

    return render(request, 'accounts/add_drywall_room.html', {
        'project': project,
        'rooms': rooms
    })

def sliding_window_materials(project_id):
    # Get all windows and doors for the project
    sliding_windows = Window.objects.filter(room__project_id=project_id, window_type='sliding')
    multi_bolt_windows = Window.objects.filter(room__project_id=project_id, window_type='multi_bolt')
    sliding_doors = Door.objects.filter(room__project_id=project_id, door_type='sliding')
    multi_bolt_doors = Door.objects.filter(room__project_id=project_id, door_type='multi_bolt')

    # Initialize data structures
    frame_data = []
    sash_data = []

    frame_totals = {
        "top": 0,
        "bottom": 0,
        "side": 0
    }

    sash_totals = {
        "top_bottom": 0,
        "handle_side": 0,  # צד
        "side": 0          # שולב
    }

    # Helper function to process items (windows or doors)
    def process_items(items, item_type):
        for item in items:
            # Get frame and sashes based on item type
            if item_type == 'window':
                frame = item.window_frame
                sashes = item.window_sashes.all()
                item_number = item.window_number
                item_subtype = item.window_type
            else:  # door
                frame = item.door_frame
                sashes = item.door_sashes.all()
                item_number = item.door_number
                item_subtype = item.door_type

            sash_count = sashes.count()

            # --- Frame Processing ---
            top = float(frame.top or 0)
            bottom = float(frame.bottom or 0)
            side = float(frame.side or 0) * 2  # both sides

            frame_data.append({
                "item_type": item_type,
                "item_subtype": item_subtype,
                "item_number": item_number,
                "top": top,
                "bottom": bottom,
                "side": side
            })

            frame_totals["top"] += top
            frame_totals["bottom"] += bottom
            frame_totals["side"] += side

            # --- Sashes Processing ---
            for i, sash in enumerate(sashes):
                sash_number = i + 1
                sash_side_length = float(sash.side or 0)
                sash_top = float(sash.top or 0)
                sash_bottom = float(sash.bottom or 0)

                handle_side = 0
                side_profile = 0

                if item_subtype == 'sliding':
                    # For sliding: first or last sash is handle-side
                    if i == 0 or i == sash_count - 1:
                        handle_side = sash_side_length
                        side_profile = sash_side_length
                    else:
                        side_profile = sash_side_length * 2
                else:  # multi_bolt
                    # For multi-bolt: all sashes need handle-side profiles
                    handle_side = sash_side_length
                    side_profile = sash_side_length

                sash_data.append({
                    "item_type": item_type,
                    "item_subtype": item_subtype,
                    "item_number": item_number,
                    "sash_number": sash_number,
                    "top": sash_top,
                    "bottom": sash_bottom,
                    "handle_side": handle_side,
                    "side": side_profile
                })

                # Accumulate totals
                sash_totals["top_bottom"] += sash_top + sash_bottom
                sash_totals["handle_side"] += handle_side
                sash_totals["side"] += side_profile

    # Process all item types
    process_items(sliding_windows, 'window')
    process_items(multi_bolt_windows, 'window')
    process_items(sliding_doors, 'door')
    process_items(multi_bolt_doors, 'door')

    # --- Calculate how many 6-meter bars needed ---
    frame_bars = {
        "top": ceil(frame_totals["top"] / 600),
        "bottom": ceil(frame_totals["bottom"] / 600),
        "side": ceil(frame_totals["side"] / 600)
    }

    sash_bars = {
        "top_bottom": ceil(sash_totals["top_bottom"] / 600),
        "handle_side": ceil(sash_totals["handle_side"] / 600),
        "side": ceil(sash_totals["side"] / 600)
    }

    return {
        "frame_data": frame_data,
        "frame_totals": frame_totals,
        "frame_bars": frame_bars,
        "sash_data": sash_data,
        "sash_totals": sash_totals,
        "sash_bars": sash_bars,
        "counts": {
            "sliding_windows": sliding_windows.count(),
            "multi_bolt_windows": multi_bolt_windows.count(),
            "sliding_doors": sliding_doors.count(),
            "multi_bolt_doors": multi_bolt_doors.count()
        }
    }



def detailed_glass_materials(project_id):
    project = Project.objects.get(id=project_id)
    glass_details = []

    for room in project.rooms.all():
        # Windows
        for window in room.windows.all():
            for sash in window.window_sashes.all():
                glass = sash.glass
                if glass:
                    area = (glass.height * glass.width).quantize(Decimal('0.01'), rounding=ROUND_UP)
                    cost = (area * glass.price).quantize(Decimal('0.01'), rounding=ROUND_UP) if glass.price else Decimal('0.00')
                    glass_details.append({
                        'item': f"Window {window.window_number}",
                        'glass_type': glass.glass_type,
                        'height': glass.height,
                        'width': glass.width,
                        'area': area,
                        'price': cost
                    })

        # Doors
        for door in room.doors.all():
            for sash in door.door_sashes.all():
                glass = sash.glass
                if glass:
                    area = (glass.height * glass.width).quantize(Decimal('0.01'), rounding=ROUND_UP)
                    cost = (area * glass.price).quantize(Decimal('0.01'), rounding=ROUND_UP) if glass.price else Decimal('0.00')
                    glass_details.append({
                        'item': f"Door {door.door_number}",
                        'glass_type': glass.glass_type,
                        'height': glass.height,
                        'width': glass.width,
                        'area': area,
                        'price': cost
                    })

    return glass_details


def get_worker_logs(worker_id, project_id):
    """
    Return logs for a specific worker and project, for completed attendance days (flag == 2).
    """
    logs = Attendance.objects.filter(
        worker_id=worker_id,
        project_id=project_id,
        flag=2
    ).order_by('date')

    log_list = []
    for log in logs:
        total_hours = 0
        if log.clock_in and log.clock_out:
            total_hours = round((log.clock_out - log.clock_in).total_seconds() / 3600, 2)
        log_list.append([
            log.date.strftime("%Y-%m-%d"),
            log.clock_in.strftime("%H:%M") if log.clock_in else "-",
            log.clock_out.strftime("%H:%M") if log.clock_out else "-",
            total_hours
        ])

    return log_list

def generate_pdf(title, headers, rows, output_path):

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, title)
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    header_line = " | ".join(headers)
    c.drawString(2 * cm, y, header_line)
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)

    for row in rows:
        line = " | ".join(str(item) for item in row)
        c.drawString(2 * cm, y, line)
        y -= 0.5 * cm
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 10)

    c.showPage()
    c.save()


@login_required
def export_drywall_materials_pdf(request, project_id):
    project = get_object_or_404(Project, id=project_id, contractor=request.user)
    walls = Wall.objects.filter(room__project=project)
    ceilings = Ceiling.objects.filter(room__project=project)

    rows = []

    # Process walls
    for i, wall in enumerate(walls, start=1):
        wall_data = calculate_wall_materials(wall)
        rows.append([
            f"Wall {i}",
            wall_data['room'],
            f"{wall_data['width']:.2f} m",
            f"{wall_data['height']:.2f} m",
            f"{wall_data['area']:.2f} m²",
            wall_data['drywall_type'],
            wall_data['stud_thickness'],
            f"{wall_data['track_length']:.2f} m",
            f"{wall_data['track_count']}",
            f"{wall_data['stud_count']}",
            f"{wall_data['hangers']}",
            f"{wall_data['gypsum_boards']}",
        ])

    # Process ceilings
    for i, ceiling in enumerate(ceilings, start=1):
        ceiling_data = calculate_wall_materials(ceiling)  # Same function handles both
        rows.append([
            f"Ceiling {i}",
            ceiling_data['room'],
            "-",  # No width for ceiling
            "-",  # No height for ceiling
            f"{ceiling_data['area']:.2f} m²",
            ceiling_data['drywall_type'],
            ceiling_data['stud_thickness'],
            f"{ceiling_data['track_length']:.2f} m",
            f"{ceiling_data['track_count']}",
            f"{ceiling_data['stud_count']}",
            f"{ceiling_data['hangers']}",
            f"{ceiling_data['gypsum_boards']}",
        ])

    headers = [
        "Item",
        "Room",
        "Width",
        "Height",
        "Area",
        "Drywall Type",
        "Stud Thickness",
        "Track Length",
        "Track Count",
        "Stud Count",
        "Hangers",
        "Gypsum Boards"
    ]

    # Define output PDF path (in contractor folder)
    output_path = os.path.join(
        settings.BASE_DIR,
        'contractors',
        request.user.username,
        'materials',
        f'drywall_materials_project_{project.project_number}.pdf'
    )

    generate_pdf(f"Drywall Materials for Project {project.project_number}", headers, rows, output_path)

    return FileResponse(open(output_path, 'rb'), content_type='application/pdf')

@login_required
def export_aluminum_materials_pdf(request, project_id):
    project = get_object_or_404(Project, id=project_id, contractor=request.user)
    aluminum_data = sliding_window_materials(project)

    headers = ["Window", "Top Frame", "Bottom Frame", "Side Frame"]
    rows = []

    # Frame rows
    for frame in aluminum_data['frame_data']:
        rows.append([
            f"Window {frame['window_number']}",
            f"{frame['top']} cm",
            f"{frame['bottom']} cm",
            f"{frame['side']} cm"
        ])
    rows.append(["TOTAL", aluminum_data['frame_totals']['top'], aluminum_data['frame_totals']['bottom'], aluminum_data['frame_totals']['side']])
    rows.append(["BARS NEEDED", aluminum_data['frame_bars']['top'], aluminum_data['frame_bars']['bottom'], aluminum_data['frame_bars']['side']])

    headers2 = ["Window", "Sash #", "Top", "Bottom", "Handle Side (צד)", "Side (שולב)"]
    rows2 = []

    # Sash rows
    for sash in aluminum_data['sash_data']:
        rows2.append([
            f"Window {sash['window_number']}",
            sash['sash_number'],
            f"{sash['top']} cm",
            f"{sash['bottom']} cm",
            f"{sash['handle_side']} cm",
            f"{sash['side']} cm"
        ])
    rows2.append(["TOTAL", "", aluminum_data['sash_totals']['top_bottom'], "", aluminum_data['sash_totals']['handle_side'], aluminum_data['sash_totals']['side']])
    rows2.append(["BARS NEEDED", "", aluminum_data['sash_bars']['top_bottom'], "", aluminum_data['sash_bars']['handle_side'], aluminum_data['sash_bars']['side']])

    output_path = os.path.join(
        settings.BASE_DIR, 'contractors', request.user.username, 'materials',
        f'aluminum_materials_project_{project.project_number}.pdf'
    )

    # Create PDF with two tables
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, f"Aluminum Frame Materials - Project {project.project_number}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, " | ".join(headers))
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    for row in rows:
        c.drawString(2 * cm, y, " | ".join(str(x) for x in row))
        y -= 0.5 * cm

    y -= 1 * cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, f"Sash Materials")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, " | ".join(headers2))
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    for row in rows2:
        c.drawString(2 * cm, y, " | ".join(str(x) for x in row))
        y -= 0.5 * cm

    c.showPage()
    c.save()

    return FileResponse(open(output_path, 'rb'), content_type='application/pdf')

@login_required
def export_glass_materials_pdf(request, project_id):
    project = get_object_or_404(Project, id=project_id, contractor=request.user)
    glass_data = detailed_glass_materials(project_id)

    headers = ["Window", "Glass Type", "Height (cm)", "Width (cm)", "Area (m²)", "Price (₪)"]
    rows = [
        [
            g['window_number'],
            g['glass_type'],
            g['height'],
            g['width'],
            g['area'],
            g['cost']
        ]
        for g in glass_data
    ]

    output_path = os.path.join(
        settings.BASE_DIR,
        'contractors',
        request.user.username,
        'materials',
        f'glass_materials_project_{project.project_number}.pdf'
    )

    generate_pdf(f"Glass Materials for Project {project.project_number}", headers, rows, output_path)

    return FileResponse(open(output_path, 'rb'), content_type='application/pdf')


@login_required
def export_worker_log_pdf(request, worker_id):
    worker = get_object_or_404(CustomUser, id=worker_id)
    contractor = request.user
    company = contractor.company

    reports = MonthlyReport.objects.filter(worker=worker).order_by('year', 'month')

    save_dir = os.path.join(settings.BASE_DIR, 'contractors', contractor.username, 'workers_log')
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{worker.username}_log.pdf"
    file_path = os.path.join(save_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, "Worker Log Summary")
    y -= 1 * cm

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, y, f"Company: {company.name}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Contractor: {contractor.username}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Worker: {worker.username}")
    y -= 1 * cm

    # Table header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5 * cm, y, "Year")
    c.drawString(3.2 * cm, y, "Month")
    c.drawString(5 * cm, y, "Days")
    c.drawString(6.5 * cm, y, "Hours")
    c.drawString(8.5 * cm, y, "Salary")
    c.drawString(11.5 * cm, y, "Payroll")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)

    # Rows
    for report in reports:
        salary = Decimal(str(report.total_hours)) * worker.hourly_wage
        c.drawString(1.5 * cm, y, str(report.year))
        c.drawString(3.2 * cm, y, str(report.month))
        c.drawString(5 * cm, y, str(report.total_days))
        c.drawString(6.5 * cm, y, f"{report.total_hours:.2f}")
        c.drawString(8.5 * cm, y, f"{salary:.2f} ₪")
        c.drawString(11.5 * cm, y, "✔" if report.payroll_file else "❌")
        y -= 0.5 * cm

        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 10)

    c.save()
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)


@login_required
def worker_work_page(request):
    user = request.user
    if user.user_type != 'worker':
        return HttpResponseForbidden("You are not allowed here.")

    projects = user.assigned_projects.filter(project_type='aluminum')

    selected_project = None
    aluminum_data = None

    if 'project_id' in request.GET:
        project_id = request.GET.get('project_id')
        selected_project = get_object_or_404(Project, id=project_id, workers=user)

        aluminum_data = sliding_window_materials(project_id)

    return render(request, 'accounts/worker_work_page.html', {
        'projects': projects,
        'selected_project': selected_project,
        'aluminum_data': aluminum_data,
    })


def calculate_wall_materials(wall):
    # Check if it's a wall or ceiling
    if hasattr(wall, 'width'):  # It's a wall
        # Convert cm to meters
        width = float(wall.width) / 100  # Convert cm to meters
        height = float(wall.height) / 100  # Convert cm to meters
        area = width * height
        layers = wall.number_of_layers
        faces = 2 if wall.double_sided else 1
        item_type = 'wall'
    else:  # It's a ceiling
        area = float(wall.area)  # Already in square meters
        # Assume square-ish ceiling for calculation purposes
        width = math.sqrt(area)
        height = area / width
        layers = 1  # Ceilings typically have 1 layer
        faces = 1  # Ceilings are single-sided
        item_type = 'ceiling'

    board_width = 1.2  # standard gypsum board width in meters
    board_height = float(wall.board_length)  # comes from board_length

    result = {
        'item_id': wall.id,
        'item_type': item_type,
        'room': wall.room.name,
        'width': width,
        'height': height,
        'area': area,
        'drywall_type': wall.get_drywall_type_display(),
        'stud_thickness': wall.get_stud_thickness_display(),
        'board_length': board_height,
        'layers': layers,
        'faces': faces,
    }

    if item_type == 'wall':
        # Wall calculations
        # Tracks (top + bottom)
        track_length = width * 2
        result['track_length'] = round(track_length, 2)
        result['track_count'] = math.ceil(track_length / 3)  # 3m standard track lengths

        # Studs
        stud_spacing = 0.4  # 40cm spacing
        stud_count = math.ceil(width / stud_spacing) + 1  # +1 for end stud

        # Calculate how many 3m studs needed based on height
        studs_per_height = math.ceil(height / 3)
        total_studs = stud_count * studs_per_height

        result['stud_count'] = total_studs
        result['hangers'] = 0  # Walls don't need hangers

    else:  # ceiling
        # Ceiling calculations - your simplified method
        # Calculate approximate length from square root of area
        length = math.sqrt(area)

        # Track length = length * 2
        track_length = length * 2
        result['track_length'] = round(track_length, 2)

        # Track count = track_length / 3 + 1
        result['track_count'] = math.ceil(track_length / 3) + 1

        # Stud count = length / 0.4 (every 40cm)
        stud_count = math.ceil(length / 0.4)

        # Calculate how many 3m studs needed based on ceiling height (assume 2.5m standard)
        ceiling_height = 2.5  # standard ceiling height in meters
        studs_per_height = math.ceil(ceiling_height / 3)
        total_studs = stud_count * studs_per_height

        result['stud_count'] = total_studs
        result['hangers'] = 0  # Not using hangers in your calculation

    # Boards (same calculation for both)
    board_area = board_width * board_height
    board_count = math.ceil(area / board_area) * layers * faces
    result['gypsum_boards'] = board_count

    return result


@login_required
def materials_page(request):
    projects = Project.objects.filter(contractor=request.user)
    selected_project = None
    aluminum_data = None
    glass_data = None
    drywall_data = None
    selected_material = None

    project_id = request.GET.get('project_id')
    action = request.GET.get('action')  # 'aluminum', 'glass', or 'drywall'

    if project_id:
        selected_project = get_object_or_404(Project, id=project_id, contractor=request.user)

        if action == 'aluminum':
            aluminum_data = sliding_window_materials(selected_project)
            selected_material = 'aluminum'

        elif action == 'glass':
            glass_data = detailed_glass_materials(selected_project.id)
            selected_material = 'glass'

        elif action == 'drywall':
            walls = Wall.objects.filter(room__project=selected_project)
            ceilings = Ceiling.objects.filter(room__project=selected_project)
            drywall_data = []

            # Process walls
            wall_counter = 1
            for wall in walls:
                wall_data = calculate_wall_materials(wall)
                wall_data['wall_number'] = wall_counter
                drywall_data.append(wall_data)
                wall_counter += 1

            # Process ceilings
            ceiling_counter = 1
            for ceiling in ceilings:
                ceiling_data = calculate_wall_materials(ceiling)
                ceiling_data['ceiling_number'] = ceiling_counter
                drywall_data.append(ceiling_data)
                ceiling_counter += 1

            selected_material = 'drywall'

    return render(request, 'accounts/materials_page.html', {
        'projects': projects,
        'selected_project': selected_project,
        'selected_material': selected_material,
        'aluminum_data': aluminum_data,
        'glass_data': glass_data,
        'drywall_data': drywall_data,
    })


@login_required
def add_screw(request):
    if request.user.user_type != 'supplier':
        return redirect('login')

    form = ScrewForm(request.POST or None)
    if form.is_valid():
        screw = form.save(commit=False)
        screw.supplier = request.user
        screw.save()
        return redirect('supplier_page')
    return render(request, 'materials/add_screw.html', {'form': form})


@login_required
def add_profile_set(request):
    if request.user.user_type != 'supplier':
        return redirect('login')

    form = ProfileSetForm(request.POST or None)
    if form.is_valid():
        profile_set = form.save(commit=False)
        profile_set.supplier = request.user
        profile_set.save()
        return redirect('supplier_page')
    return render(request, 'materials/add_profile_set.html', {'form': form})


@login_required
def add_metal_profile(request):
    if request.user.user_type != 'supplier':
        return redirect('login')

    form = MetalProfileForm(request.POST or None)
    if form.is_valid():
        metal = form.save(commit=False)
        metal.supplier = request.user
        metal.save()
        return redirect('supplier_page')
    return render(request, 'materials/add_metal_profile.html', {'form': form})


@login_required
def add_drywall_board(request):
    if request.user.user_type != 'supplier':
        return redirect('login')

    form = DrywallBoardForm(request.POST or None)
    if form.is_valid():
        board = form.save(commit=False)
        board.supplier = request.user
        board.save()
        return redirect('supplier_page')
    return render(request, 'materials/add_drywall_board.html', {'form': form})


@login_required
def edit_screw(request, pk):
    screw = get_object_or_404(Screw, pk=pk, supplier=request.user)
    form = ScrewForm(request.POST or None, instance=screw)
    if form.is_valid():
        form.save()
        messages.success(request, "Screw updated.")
        return redirect('supplier_home')
    return render(request, 'accounts/edit_item.html', {'form': form, 'title': 'Edit Screw'})

@login_required
def delete_screw(request, pk):
    screw = get_object_or_404(Screw, pk=pk, supplier=request.user)
    if request.method == 'POST':
        screw.delete()
        messages.success(request, "Screw deleted.")
        return redirect('supplier_home')
    return render(request, 'accounts/delete_confirm.html', {'item': screw})


# --- Profile Set ---
@login_required
def edit_profile_set(request, pk):
    profile = get_object_or_404(ProfileSet, pk=pk, supplier=request.user)
    form = ProfileSetForm(request.POST or None, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile set updated.")
        return redirect('supplier_home')
    return render(request, 'accounts/edit_item.html', {'form': form, 'title': 'Edit Aluminum Profile Set'})

@login_required
def delete_profile_set(request, pk):
    profile = get_object_or_404(ProfileSet, pk=pk, supplier=request.user)
    if request.method == 'POST':
        profile.delete()
        messages.success(request, "Profile set deleted.")
        return redirect('supplier_home')
    return render(request, 'accounts/delete_confirm.html', {'item': profile})


# --- Metal Profile ---
@login_required
def edit_metal_profile(request, pk):
    metal = get_object_or_404(MetalProfile, pk=pk, supplier=request.user)
    form = MetalProfileForm(request.POST or None, instance=metal)
    if form.is_valid():
        form.save()
        messages.success(request, "Metal profile updated.")
        return redirect('supplier_home')
    return render(request, 'accounts/edit_item.html', {'form': form, 'title': 'Edit Stud/Track'})

@login_required
def delete_metal_profile(request, pk):
    metal = get_object_or_404(MetalProfile, pk=pk, supplier=request.user)
    if request.method == 'POST':
        metal.delete()
        messages.success(request, "Metal profile deleted.")
        return redirect('supplier_home')
    return render(request, 'accounts/delete_confirm.html', {'item': metal})


# --- Drywall Board ---
@login_required
def edit_drywall_board(request, pk):
    board = get_object_or_404(DrywallBoard, pk=pk, supplier=request.user)
    form = DrywallBoardForm(request.POST or None, instance=board)
    if form.is_valid():
        form.save()
        messages.success(request, "Board updated.")
        return redirect('supplier_home')
    return render(request, 'accounts/edit_item.html', {'form': form, 'title': 'Edit Drywall Board'})

@login_required
def delete_drywall_board(request, pk):
    board = get_object_or_404(DrywallBoard, pk=pk, supplier=request.user)
    if request.method == 'POST':
        board.delete()
        messages.success(request, "Board deleted.")
        return redirect('supplier_home')
    return render(request, 'accounts/delete_confirm.html', {'item': board})

@login_required
def supplier_add_items(request):
    if request.user.user_type != 'supplier':
        return redirect('login')

    # Forms
    screw_form = ScrewForm(request.POST or None, prefix='screw')
    profile_set_form = ProfileSetForm(request.POST or None, prefix='profile')
    metal_form = MetalProfileForm(request.POST or None, prefix='metal')
    board_form = DrywallBoardForm(request.POST or None, prefix='board')

    # Form submission
    if request.method == 'POST':
        if 'submit_screw' in request.POST and screw_form.is_valid():
            obj = screw_form.save(commit=False)
            obj.supplier = request.user
            obj.save()
            return redirect('supplier_add_items')

        elif 'submit_profile' in request.POST and profile_set_form.is_valid():
            obj = profile_set_form.save(commit=False)
            obj.supplier = request.user
            obj.save()
            return redirect('supplier_add_items')

        elif 'submit_metal' in request.POST and metal_form.is_valid():
            obj = metal_form.save(commit=False)
            obj.supplier = request.user
            obj.save()
            return redirect('supplier_add_items')

        elif 'submit_board' in request.POST and board_form.is_valid():
            obj = board_form.save(commit=False)
            obj.supplier = request.user
            obj.save()
            return redirect('supplier_add_items')

    # Get existing items to display
    screws = Screw.objects.filter(supplier=request.user)
    profile_sets = ProfileSet.objects.filter(supplier=request.user)
    metal_profiles = MetalProfile.objects.filter(supplier=request.user)
    boards = DrywallBoard.objects.filter(supplier=request.user)

    return render(request, 'accounts/supplier_add_items.html', {
        'screw_form': screw_form,
        'profile_set_form': profile_set_form,
        'metal_form': metal_form,
        'board_form': board_form,
        'screws': screws,
        'profile_sets': profile_sets,
        'metal_profiles': metal_profiles,
        'boards': boards,
    })

@login_required
def supplier_home_view(request):
    if request.user.user_type != 'supplier':
        return redirect('login')

    screws = Screw.objects.filter(supplier=request.user)
    profile_sets = ProfileSet.objects.filter(supplier=request.user)
    metal_profiles = MetalProfile.objects.filter(supplier=request.user)
    boards = DrywallBoard.objects.filter(supplier=request.user)

    return render(request, 'accounts/supplier_home.html', {
        'screws': screws,
        'profile_sets': profile_sets,
        'metal_profiles': metal_profiles,
        'boards': boards,
    })

@login_required
def supplier_list_view(request):
    if request.user.user_type != 'contractor':
        return redirect('login')

    suppliers = CustomUser.objects.filter(user_type='supplier')
    return render(request, 'accounts/supplier_list.html', {'suppliers': suppliers})
@login_required
def supplier_inventory_view(request, supplier_id):
    if request.user.user_type != 'contractor':
        return redirect('login')

    supplier = get_object_or_404(CustomUser, id=supplier_id, user_type='supplier')

    screws = Screw.objects.filter(supplier=supplier)
    profile_sets = ProfileSet.objects.filter(supplier=supplier)
    metal_profiles = MetalProfile.objects.filter(supplier=supplier)
    boards = DrywallBoard.objects.filter(supplier=supplier)

    if request.method == 'POST':
        material_type = request.POST.get('material_type')
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))

        item_description = ''
        item_name = ''
        unit_price = 0

        if material_type == 'screw':
            item = get_object_or_404(Screw, pk=item_id)
            item_description = f"{item.screw_type} {item.length_cm}cm ({item.count_per_box} pcs)"
            item_name = item.screw_type
            unit_price = item.price_per_100
        elif material_type == 'profile':
            item = get_object_or_404(ProfileSet, pk=item_id)
            item_description = f"{item.name} ({item.kind})"
            item_name = item.name
            unit_price = item.price_per_kilo
        elif material_type == 'metal':
            item = get_object_or_404(MetalProfile, pk=item_id)
            item_description = f"{item.profile_type} {item.size}"
            item_name = item.profile_type
            unit_price = item.price_per_piece
        elif material_type == 'board':
            item = get_object_or_404(DrywallBoard, pk=item_id)
            item_description = f"{item.color} {item.size}"
            item_name = item.color
            unit_price = item.price_per_board

        # Check for an existing pending order with same contractor + supplier
        order = Order.objects.filter(contractor=request.user, supplier=supplier, status='pending').first()
        if not order:
            order = Order.objects.create(
                contractor=request.user,
                supplier=supplier,
                item_description=item_description
            )

        # Add item to the order
        OrderItem.objects.create(
            order=order,
            item_name=item_name,
            unit_price=unit_price,
            quantity=quantity
        )

        messages.success(request, "Order placed successfully.")
        return redirect('supplier_inventory', supplier_id=supplier.id)

    return render(request, 'accounts/supplier_inventory.html', {
        'supplier': supplier,
        'screws': screws,
        'profile_sets': profile_sets,
        'metal_profiles': metal_profiles,
        'boards': boards,
    })

@login_required
def supplier_orders_view(request):
    if request.user.user_type != 'supplier':
        return redirect('supplier_login')

    orders = Order.objects.filter(supplier=request.user).prefetch_related('items', 'company', 'contractor')

    for order in orders:
        order.delivery_form = DeliveryDateForm(initial={'delivery_date': order.delivery_date})

    return render(request, 'accounts/supplier_orders.html', {'orders': orders})



@transaction.atomic
def create_or_update_order(request, supplier, item_name, unit_price, quantity):
    contractor = request.user
    company = contractor.company

    # Try to get an existing pending order
    order = Order.objects.filter(
        contractor=contractor,
        supplier=supplier,
        company=company,
        status='pending'
    ).first()

    if not order:
        # Step 1: Create with guaranteed-unique temporary value
        unique_temp = f"TEMP-{uuid.uuid4().hex[:8]}"
        order = Order.objects.create(
            contractor=contractor,
            supplier=supplier,
            company=company,
            order_number=unique_temp,
            status='pending'
        )

        # Step 2: Now set the readable order number with order ID
        order.order_number = f"ORD{datetime.now().strftime('%Y%m%d')}-{order.id}"
        order.save()

    # Add or update item
    item = order.items.filter(item_name=item_name, unit_price=unit_price).first()
    if item:
        item.quantity += quantity
        item.save()
    else:
        OrderItem.objects.create(
            order=order,
            item_name=item_name,
            unit_price=unit_price,
            quantity=quantity
        )

    return order

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        date_form = DeliveryDateForm(request.POST)

        # Update delivery date
        if date_form.is_valid():
            order.delivery_date = date_form.cleaned_data['delivery_date']

        # Only update status if it's present in POST data
        if status:
            order.status = status

        order.save()
        return redirect('supplier_orders')




@login_required
def contractor_orders_view(request):
    orders = Order.objects.filter(contractor=request.user)
    return render(request, 'accounts/contractor_orders.html', {'orders': orders})

def generate_order_pdf(order):
    folder_path = os.path.join("contractors", order.contractor.username, "orders")
    os.makedirs(folder_path, exist_ok=True)

    filename = f"order_{order.order_number}.pdf"
    filepath = os.path.join(folder_path, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Order Number: {order.order_number}")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Contractor: {order.contractor.name}")
    y -= 20
    c.drawString(50, y, f"Company: {order.company.name if order.company else 'N/A'}")
    y -= 20
    c.drawString(50, y, f"Supplier: {order.supplier.name}")
    y -= 20
    c.drawString(50, y, f"Status: {order.status}")
    y -= 20
    c.drawString(50, y, f"Date Created: {order.created_at.strftime('%Y-%m-%d')}")
    y -= 20
    if order.delivery_date:
        c.drawString(50, y, f"Delivery Date: {order.delivery_date.strftime('%Y-%m-%d')}")
        y -= 20

    y -= 20
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Items:")
    y -= 20
    c.setFont("Helvetica", 12)
    for item in order.items.all():
        line = f"{item.item_name} — {item.quantity} pcs @ ₪{item.unit_price} = ₪{item.total_price()}"
        c.drawString(60, y, line)
        y -= 18
        if y < 100:
            c.showPage()
            y = height - 50

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Total Before Tax: ₪{order.total_before_tax():.2f}")
    y -= 20
    c.drawString(50, y, f"Total After Tax (18%): ₪{order.total_after_tax():.2f}")

    c.save()
    return filepath

@login_required
def export_order_pdf_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, contractor=request.user)
    filepath = generate_order_pdf(order)
    return HttpResponse(f"PDF generated at: {filepath}")


