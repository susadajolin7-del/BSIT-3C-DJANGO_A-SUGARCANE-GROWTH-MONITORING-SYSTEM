from django.db import models
from django.contrib.auth.models import User
from apps.core.models import Farmer


class FarmerAccount(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='farmer_account'
    )

    farmer = models.OneToOneField(
        Farmer,
        on_delete=models.CASCADE,
        related_name='user_account'
    )

    class Meta:
        db_table = 'farmer_accounts'

    def __str__(self):
        return f"{self.farmer.first_name} {self.farmer.last_name}"