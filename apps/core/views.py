from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Farmer, SugarcaneField, CropCycle, GrowthRecord, HarvestRecord
User = get_user_model()

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=1)
INVALID_LOGIN_MESSAGE = 'Invalid username or password.'
LOCKED_MESSAGE = 'Too many failed attempts. Locked for 1 minute.'


def _reset_lock_state(request):
    request.session['failed_attempts'] = 0
    request.session['lock_time'] = None


def _get_lock_state(request):
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')

    if not lock_time:
        return failed_attempts, None

    try:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
    except (TypeError, ValueError):
        _reset_lock_state(request)
        return 0, None

    if timezone.now() < unlock_time:
        remaining = int((unlock_time - timezone.now()).total_seconds())
        return failed_attempts, remaining

    _reset_lock_state(request)
    return 0, None


def _set_lock_state(request):
    lock_until = timezone.now() + LOCK_DURATION
    request.session['failed_attempts'] = MAX_FAILED_ATTEMPTS
    request.session['lock_time'] = lock_until.isoformat()
    return int(LOCK_DURATION.total_seconds())


def _validate_registration_data(data):
    errors = {}

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username:
        errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already taken.'

    if not first_name:
        errors['first_name'] = 'First name is required.'

    if not last_name:
        errors['last_name'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address.'
        else:
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors['password'] = ' '.join(exc.messages)

    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    return errors


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    failed_attempts, remaining = _get_lock_state(request)
    if remaining is not None:
        messages.error(request, f'Too many failed attempts. Try again in {remaining} seconds.')
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    if request.method == 'GET':
        return render(request, 'auth/login.html')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        _reset_lock_state(request)
        login(request, user)
        return redirect('dashboard')

    failed_attempts += 1
    request.session['failed_attempts'] = failed_attempts
    if failed_attempts >= MAX_FAILED_ATTEMPTS:
        remaining = _set_lock_state(request)
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/login.html', {'locked': True, 'remaining': remaining})

    remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
    messages.error(request, f'{INVALID_LOGIN_MESSAGE} {remaining_attempts} attempts remaining.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home(request):
    growth_records = GrowthRecord.objects.exclude(
        growth_height_cm__isnull=True
    ).order_by('record_date')

    growth_trend = [
        [
            record.record_date.isoformat(),
            float(record.growth_height_cm)
        ]
        for record in growth_records
    ]

    

    # Get crop varieties using crop_id
    crop_varieties = dict(
        CropCycle.objects.values_list('crop_id', 'variety')
    )

    variety_totals = {}

    for record in GrowthRecord.objects.exclude(
        growth_height_cm__isnull=True
    ).values('crop_id', 'growth_height_cm'):

        variety = crop_varieties.get(record['crop_id'])

        if variety:
            if variety not in variety_totals:
                variety_totals[variety] = {
                    'total': 0,
                    'count': 0
                }

            variety_totals[variety]['total'] += float(
                record['growth_height_cm']
            )
            variety_totals[variety]['count'] += 1

    variety_growth = [
        [
            variety,
            round(values['total'] / values['count'], 2)
        ]
        for variety, values in variety_totals.items()
    ]

    context = {
        'total_farmers': Farmer.objects.count(),
        'total_fields': SugarcaneField.objects.count(),
        'fields': SugarcaneField.objects.all(),
        'total_crop_cycles': CropCycle.objects.count(),

        'active_varieties': CropCycle.objects.exclude(
            variety__isnull=True
        ).exclude(variety='').values('variety').distinct().count(),

        'varieties': CropCycle.objects.exclude(
            variety__isnull=True
        ).exclude(variety='').values('variety').distinct(),

        'total_growth_records': GrowthRecord.objects.count(),

        'growth_records': GrowthRecord.objects.all().order_by('-record_date'),

        'total_harvest_records': HarvestRecord.objects.count(),

        'average_height': GrowthRecord.objects.aggregate(
            avg_height=Avg('growth_height_cm')
        )['avg_height'] or 0,

        'growth_trend': growth_trend,
        'variety_growth': variety_growth,
    }

    return render(request, 'home.html', context)

    
@login_required(login_url='login')
def farmers_list(request):
    farmers = Farmer.objects.all()
    return render(request, 'farmers/list.html', {
        'farmers': farmers
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def farmer_add(request):

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not first_name or not last_name:
            messages.error(
                request,
                'First Name and Last Name are required.'
            )
            return render(request, 'farmers/add.html')

        Farmer.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone or None,
            address=address or None
        )

        messages.success(
            request,
            'Farmer successfully added!'
        )

        return redirect('farmers')

    return render(request, 'farmers/add.html')

@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def farmer_edit(request, farmer_id):
    farmer = Farmer.objects.get(farmer_id=farmer_id)


    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not first_name or not last_name:
            messages.error(request, 'First Name and Last Name are required.')
            return render(request, 'farmers/edit.html', {
                'farmer': farmer
            })

        farmer.first_name = first_name
        farmer.last_name = last_name
        farmer.phone = phone or None
        farmer.address = address or None
        farmer.save()

        messages.success(request, 'Farmer successfully updated!')
        return redirect('farmers')

    return render(request, 'farmers/edit.html', {
        'farmer': farmer
    })
@login_required(login_url='login')
@require_http_methods(['POST'])
def farmer_delete(request, farmer_id):
    farmer = get_object_or_404(Farmer, farmer_id=farmer_id)

    farmer.delete()

    messages.success(request, 'Farmer successfully deleted!')
    return redirect('farmers')



@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'GET':
        return render(request, 'auth/register.html')

    form_data = {
        'username': request.POST.get('username', ''),
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'email': request.POST.get('email', ''),
        'password': request.POST.get('password', ''),
        'confirm_password': request.POST.get('confirm_password', ''),
    }

    errors = _validate_registration_data(form_data)
    if errors:
        return render(request, 'auth/register.html', {'errors': errors, 'form_data': form_data})

    user = User.objects.create_user(
        username=form_data['username'].strip(),
        first_name=form_data['first_name'].strip(),
        last_name=form_data['last_name'].strip(),
        email=form_data['email'].strip(),
        password=form_data['password'],
    )
    login(request, user)
    return redirect('dashboard')

@login_required(login_url='login')
def fields_list(request):
    fields = SugarcaneField.objects.all()
    return render(request, 'fields/list.html', {
        'fields': fields
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def field_add(request):
    if request.method == 'POST':
        farmer_id = request.POST.get('farmer_id', '').strip()
        field_name = request.POST.get('field_name', '').strip()
        location = request.POST.get('location', '').strip()
        area_hectares = request.POST.get('area_hectares', '').strip()
        soil_type = request.POST.get('soil_type', '').strip()

        if not farmer_id.isdigit():
            messages.error(request, 'Please enter a valid Farmer ID.')

        elif not Farmer.objects.filter(farmer_id=farmer_id).exists():
            messages.error(request, 'Farmer ID does not exist.')

        elif not field_name:
            messages.error(request, 'Field Name is required.')

        else:
            SugarcaneField.objects.create(
                farmer_id=int(farmer_id),
                field_name=field_name,
                location=location or None,
                area_hectares=area_hectares or None,
                soil_type=soil_type or None
            )

            messages.success(request, 'Field successfully added!')
            return redirect('fields')

    return render(request, 'fields/add.html')


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def field_edit(request, field_id):
    field = get_object_or_404(SugarcaneField, field_id=field_id)

    if request.method == 'POST':
        farmer_id = request.POST.get('farmer_id', '').strip()
        field_name = request.POST.get('field_name', '').strip()
        location = request.POST.get('location', '').strip()
        area_hectares = request.POST.get('area_hectares', '').strip()
        soil_type = request.POST.get('soil_type', '').strip()

        if not farmer_id.isdigit():
            messages.error(request, 'Please enter a valid Farmer ID.')

        elif not Farmer.objects.filter(farmer_id=farmer_id).exists():
            messages.error(request, 'Farmer ID does not exist.')

        elif not field_name:
            messages.error(request, 'Field Name is required.')

        else:
            field.farmer_id = int(farmer_id)
            field.field_name = field_name
            field.location = location or None
            field.area_hectares = area_hectares or None
            field.soil_type = soil_type or None
            field.save()

            messages.success(request, 'Field successfully updated!')
            return redirect('fields')

    return render(request, 'fields/edit.html', {'field': field})


@login_required(login_url='login')
@require_http_methods(['POST'])
def field_delete(request, field_id):
    field = get_object_or_404(SugarcaneField, field_id=field_id)
    field.delete()

    messages.success(request, 'Field successfully deleted!')
    return redirect('fields')





@login_required(login_url='login')
def crop_cycles_list(request):
    today = timezone.localdate()
    crop_cycles = CropCycle.objects.all()

    for crop in crop_cycles:
        if crop.expected_harvest_date:
            estimated_date = crop.expected_harvest_date
        else:
            estimated_date = crop.planting_date + timedelta(days=365)

        crop.predicted_harvest_date = estimated_date

        if crop.status == 'Harvested':
            crop.prediction_status = 'Harvested'
        elif today >= estimated_date:
            crop.prediction_status = 'For Harvest Assessment'
        else:
            crop.prediction_status = 'Growing'

    return render(request, 'crop_cycles/list.html', {
        'crop_cycles': crop_cycles
    })

@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def crop_cycle_add(request):
    fields = SugarcaneField.objects.all()

    if request.method == 'POST':
        field_id = request.POST.get('field_id', '').strip()
        variety = request.POST.get('variety', '').strip()
        planting_date = request.POST.get('planting_date', '').strip()
        expected_harvest_date = request.POST.get('expected_harvest_date', '').strip()
        status = request.POST.get('status', 'Growing').strip()

        if not field_id.isdigit() or not SugarcaneField.objects.filter(field_id=field_id).exists():
            messages.error(request, 'Please select a valid field.')
        elif not planting_date:
            messages.error(request, 'Planting Date is required.')
        else:
            CropCycle.objects.create(
                field_id=int(field_id),
                variety=variety or None,
                planting_date=planting_date,
                expected_harvest_date=expected_harvest_date or None,
                status=status or 'Growing'
            )
            messages.success(request, 'Crop Cycle successfully added!')
            return redirect('crop_cycles')

    return render(request, 'crop_cycles/add.html', {
        'fields': fields
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def crop_cycle_edit(request, crop_id):
    crop = get_object_or_404(CropCycle, crop_id=crop_id)
    fields = SugarcaneField.objects.all()

    if request.method == 'POST':
        field_id = request.POST.get('field_id', '').strip()
        variety = request.POST.get('variety', '').strip()
        planting_date = request.POST.get('planting_date', '').strip()
        expected_harvest_date = request.POST.get('expected_harvest_date', '').strip()
        status = request.POST.get('status', 'Growing').strip()

        if not field_id.isdigit() or not SugarcaneField.objects.filter(field_id=field_id).exists():
            messages.error(request, 'Please select a valid field.')
        elif not planting_date:
            messages.error(request, 'Planting Date is required.')
        else:
            crop.field_id = int(field_id)
            crop.variety = variety or None
            crop.planting_date = planting_date
            crop.expected_harvest_date = expected_harvest_date or None
            crop.status = status or 'Growing'
            crop.save()

            messages.success(request, 'Crop Cycle successfully updated!')
            return redirect('crop_cycles')

    return render(request, 'crop_cycles/edit.html', {
        'crop': crop,
        'fields': fields
    })

@login_required(login_url='login')
@require_http_methods(['POST'])
def crop_cycle_delete(request, crop_id):
    crop = get_object_or_404(CropCycle, crop_id=crop_id)

    crop.delete()

    messages.success(request, 'Crop Cycle successfully deleted!')
    return redirect('crop_cycles')

          


@login_required(login_url='login')
def growth_records_list(request):
    growth_records = GrowthRecord.objects.all().order_by('-record_date')

    return render(request, 'growth_records/list.html', {
        'growth_records': growth_records
    })



@login_required(login_url='login')
def harvest_records_list(request):
    harvest_records = HarvestRecord.objects.all().order_by('-harvest_date')

    return render(request, 'harvest_records/list.html', {
        'harvest_records': harvest_records
    })

@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def growth_record_add(request):
    crops = CropCycle.objects.all()

    if request.method == 'POST':
        crop_id = request.POST.get('crop_id', '').strip()
        record_date = request.POST.get('record_date', '').strip()
        growth_height_cm = request.POST.get('growth_height_cm', '').strip()
        plant_weight_kg = request.POST.get('plant_weight_kg', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not crop_id.isdigit() or not CropCycle.objects.filter(crop_id=crop_id).exists():
            messages.error(request, 'Please select a valid crop cycle.')
        elif not record_date:
            messages.error(request, 'Record Date is required.')
        else:
            GrowthRecord.objects.create(
                crop_id=int(crop_id),
                record_date=record_date,
                growth_height_cm=growth_height_cm or None,
                plant_weight_kg=plant_weight_kg or None,
                notes=notes or None
            )

            messages.success(request, 'Growth Record successfully added!')
            return redirect('growth_records')

    return render(request, 'growth_records/add.html', {
        'crops': crops
    })

@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def growth_record_edit(request, record_id):
    record = get_object_or_404(GrowthRecord, record_id=record_id)
    crops = CropCycle.objects.all()

    if request.method == 'POST':
        crop_id = request.POST.get('crop_id', '').strip()
        record_date = request.POST.get('record_date', '').strip()
        growth_height_cm = request.POST.get('growth_height_cm', '').strip()
        plant_weight_kg = request.POST.get('plant_weight_kg', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not crop_id.isdigit() or not CropCycle.objects.filter(crop_id=crop_id).exists():
            messages.error(request, 'Please select a valid crop cycle.')
        elif not record_date:
            messages.error(request, 'Record Date is required.')
        else:
            record.crop_id = int(crop_id)
            record.record_date = record_date
            record.growth_height_cm = growth_height_cm or None
            record.plant_weight_kg = plant_weight_kg or None
            record.notes = notes or None
            record.save()

            messages.success(request, 'Growth Record successfully updated!')
            return redirect('growth_records')

    return render(request, 'growth_records/edit.html', {
        'record': record,
        'crops': crops
    })

@login_required(login_url='login')
@require_http_methods(['POST'])
def growth_record_delete(request, record_id):
    record = get_object_or_404(GrowthRecord, record_id=record_id)

    record.delete()

    messages.success(request, 'Growth Record successfully deleted!')
    return redirect('growth_records')

@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def harvest_record_add(request):
    crops = CropCycle.objects.all()

    if request.method == 'POST':
        crop_id = request.POST.get('crop_id', '').strip()
        harvest_date = request.POST.get('harvest_date', '').strip()
        quantity_tons = request.POST.get('quantity_tons', '').strip()
        quality_grade = request.POST.get('quality_grade', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not crop_id.isdigit() or not CropCycle.objects.filter(crop_id=crop_id).exists():
            messages.error(request, 'Please select a valid crop cycle.')
        elif not harvest_date:
            messages.error(request, 'Harvest Date is required.')
        else:
            HarvestRecord.objects.create(
                crop_id=int(crop_id),
                harvest_date=harvest_date,
                quantity_tons=quantity_tons or None,
                quality_grade=quality_grade or None,
                notes=notes or None
            )

            messages.success(request, 'Harvest Record successfully added!')
            return redirect('harvest_records')

    return render(request, 'harvest_records/add.html', {
        'crops': crops
    })

@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def harvest_record_edit(request, harvest_id):
    record = get_object_or_404(HarvestRecord, harvest_id=harvest_id)
    crops = CropCycle.objects.all()

    if request.method == 'POST':
        crop_id = request.POST.get('crop_id', '').strip()
        harvest_date = request.POST.get('harvest_date', '').strip()
        quantity_tons = request.POST.get('quantity_tons', '').strip()
        quality_grade = request.POST.get('quality_grade', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not crop_id.isdigit() or not CropCycle.objects.filter(crop_id=crop_id).exists():
            messages.error(request, 'Please select a valid crop cycle.')
        elif not harvest_date:
            messages.error(request, 'Harvest Date is required.')
        else:
            record.crop_id = int(crop_id)
            record.harvest_date = harvest_date
            record.quantity_tons = quantity_tons or None
            record.quality_grade = quality_grade or None
            record.notes = notes or None
            record.save()

            messages.success(request, 'Harvest Record successfully updated!')
            return redirect('harvest_records')

    return render(request, 'harvest_records/edit.html', {
        'record': record,
        'crops': crops
    })

@login_required(login_url='login')
@require_http_methods(['POST'])
def harvest_record_delete(request, harvest_id):
    record = get_object_or_404(HarvestRecord, harvest_id=harvest_id)

    record.delete()

    messages.success(request, 'Harvest Record successfully deleted!')
    return redirect('harvest_records')