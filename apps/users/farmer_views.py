
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import transaction, IntegrityError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.core.models import Farmer, SugarcaneField, CropCycle
from .models import FarmerAccount


def farmer_register(request):

    if request.method == 'POST':

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not all([first_name, last_name, username, password1, password2]):
            messages.error(request, 'Please complete all required fields.')
            return render(request, 'users/register.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'users/register.html')

        try:
            validate_password(password1)
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)
            return render(request, 'users/register.html')

        try:
            with transaction.atomic():
                farmer = Farmer.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    address=address
                )

                user = User.objects.create_user(
                    username=username,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name
                )

                FarmerAccount.objects.create(
                    user=user,
                    farmer=farmer
                )

            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('users:farmer_register')

        except IntegrityError:
            messages.error(request, 'Registration could not be completed. Please check your information.')

    return render(request, 'users/register.html')

def farmer_login(request):

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            if hasattr(user, 'farmer_account'):
                login(request, user)
                return redirect('users:farmer_dashboard')

            messages.error(request, 'This account is not linked to a farmer.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


def farmer_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('users:farmer_login')

    if not hasattr(request.user, 'farmer_account'):
        return redirect('users:farmer_login')

    farmer = request.user.farmer_account.farmer

    # Kunin ang fields ng naka-login na farmer
    farmer_fields = SugarcaneField.objects.filter(
        farmer_id=farmer.farmer_id
    )

    total_fields = farmer_fields.count()

    # Kunin ang crop cycles ng farmer
    farmer_cycles = CropCycle.objects.filter(
        field_id__in=farmer_fields.values_list(
            'field_id', flat=True
        )
    )

    context = {
        'farmer': farmer,
        'total_fields': total_fields,
        'active_cycles': farmer_cycles.count(),
        'total_growth_records': 0,
        'total_harvest_records': 0,
    }

    return render(
        request,
        'users/farmer_dashboard.html',
        context
    )


def farmer_logout(request):
    logout(request)
    return redirect('users:farmer_login')

def farmer_profile(request):

    if not request.user.is_authenticated:
        return redirect('users:farmer_login')

    if not hasattr(request.user, 'farmer_account'):
        return redirect('users:farmer_login')

    farmer = request.user.farmer_account.farmer

    context = {
        'farmer': farmer,
    }

    return render(request, 'users/farmer_profile.html', context)

def farmer_fields(request):

    if not request.user.is_authenticated:
        return redirect('users:farmer_login')

    if not hasattr(request.user, 'farmer_account'):
        return redirect('users:farmer_login')

    farmer = request.user.farmer_account.farmer

    fields = SugarcaneField.objects.filter(
        farmer_id=farmer.farmer_id
    )

    return render(
        request,
        'users/farmer_fields.html',
        {'fields': fields}
    )

def farmer_crop_cycles(request):

    if not request.user.is_authenticated:
        return redirect('users:farmer_login')

    if not hasattr(request.user, 'farmer_account'):
        return redirect('users:farmer_login')

    farmer = request.user.farmer_account.farmer

    farmer_fields = SugarcaneField.objects.filter(
        farmer_id=farmer.farmer_id
    )

    crops = CropCycle.objects.filter(
        field_id__in=farmer_fields.values_list('field_id', flat=True)
    )

    return render(
        request,
        'users/farmer_crop_cycles.html',
        {'crops': crops}
    )