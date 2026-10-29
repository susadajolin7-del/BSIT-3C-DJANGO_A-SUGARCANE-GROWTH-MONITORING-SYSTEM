from django.db import models

# create your models here.
from django.db import models


class Farmer(models.Model):
    farmer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'farmers'
        managed = False

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    

class SugarcaneField(models.Model):
    field_id = models.AutoField(primary_key=True)
    farmer_id = models.IntegerField()
    field_name = models.CharField(max_length=100)
    location = models.CharField(max_length=150, null=True, blank=True)
    area_hectares = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    soil_type = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'sugarcane_fields'
        managed = False

    def __str__(self):
        return self.field_name

    
class CropCycle(models.Model):
    crop_id = models.AutoField(primary_key=True)
    field_id = models.IntegerField()
    variety = models.CharField(max_length=100, null=True, blank=True)
    planting_date = models.DateField()
    expected_harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, null=True, blank=True, default='Growing')

    class Meta:
        db_table = 'crop_cycles'
        managed = False

    def __str__(self):
        return f"Crop Cycle {self.crop_id}"


class GrowthRecord(models.Model):
    record_id = models.AutoField(primary_key=True)
    crop_id = models.IntegerField()
    record_date = models.DateField()
    growth_height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    plant_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'growth_records'
        managed = False

    def __str__(self):
        return f"Growth Record {self.record_id}"



class HarvestRecord(models.Model):
    harvest_id = models.AutoField(primary_key=True)
    crop_id = models.IntegerField()
    harvest_date = models.DateField()
    quantity_tons = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    quality_grade = models.CharField(
        max_length=30, null=True, blank=True
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'harvest_records'
        managed = False

    def __str__(self):
        return f"Harvest Record {self.harvest_id}"

