
from django.shortcuts import render
from django.db import connection


def home(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM sugarcane_fields")
        total_fields = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM crop_cycles")
        total_crop_cycles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM growth_records")
        total_growth_records = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM harvest_records")
        total_harvest_records = cursor.fetchone()[0]

    context = {
        'total_fields': total_fields,
        'total_crop_cycles': total_crop_cycles,
        'total_growth_records': total_growth_records,
        'total_harvest_records': total_harvest_records,
    }

    return render(request, 'home.html', context)