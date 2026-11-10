
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
                # CHART 1: Growth Trend
        cursor.execute("""
            SELECT
                record_date,
                ROUND(AVG(growth_height_cm), 2)
            FROM growth_records
            WHERE growth_height_cm IS NOT NULL
            GROUP BY record_date
            ORDER BY record_date
        """)
        growth_trend = cursor.fetchall()

        # CHART 2: Average Height by Variety
        cursor.execute("""
            SELECT
                cc.variety,
                ROUND(AVG(gr.growth_height_cm), 2)
            FROM growth_records gr
            INNER JOIN crop_cycles cc
                ON gr.crop_id = cc.crop_id
            WHERE gr.growth_height_cm IS NOT NULL
            GROUP BY cc.variety
            ORDER BY cc.variety
        """)
        variety_growth = cursor.fetchall()

                # CHART 3: Growth Rate Data
        cursor.execute("""
            SELECT crop_id, record_date, growth_height_cm
            FROM growth_records
            WHERE growth_height_cm IS NOT NULL
            ORDER BY crop_id, record_date
        """)
        growth_measurements = cursor.fetchall()
            # COMPUTE AVERAGE DAILY GROWTH RATE
    growth_rates = []
    previous_records = {}

    for crop_id, record_date, height in growth_measurements:
        if crop_id in previous_records:
            previous_date, previous_height = previous_records[crop_id]

            days = (record_date - previous_date).days

            if days > 0:
                daily_rate = float((height - previous_height) / days)
                growth_rates.append(daily_rate)

        previous_records[crop_id] = (record_date, height)

    average_growth_rate = (
        round(sum(growth_rates) / len(growth_rates), 2)
        if growth_rates else 0
    )

    context = {
    'total_fields': total_fields,
    'total_crop_cycles': total_crop_cycles,
    'total_growth_records': total_growth_records,
    'total_harvest_records': total_harvest_records,

    'growth_trend': growth_trend,
    'variety_growth': variety_growth,
}
    

    return render(request, 'home.html', context)