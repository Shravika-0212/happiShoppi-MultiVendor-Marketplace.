from django.db import models


class User(models.Model):

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('VENDOR', 'Vendor'),
        ('CUSTOMER', 'Customer'),
    ]

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=100)

    email = models.EmailField(
        max_length=100,
        unique=True
    )

    password = models.CharField(max_length=255)

    role = models.CharField(
        max_length=8,
        choices=ROLE_CHOICES
    )

    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    address = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return self.email
