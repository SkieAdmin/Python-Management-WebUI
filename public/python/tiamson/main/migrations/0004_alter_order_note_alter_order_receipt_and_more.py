# Generated by Django 5.1.4 on 2025-05-01 22:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_remove_order_is_confirmed_order_note_order_receipt_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='note',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='receipt',
            field=models.ImageField(blank=True, null=True, upload_to='receipts/'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Awaiting Confirmation', 'Awaiting Confirmation'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled')], default='Pending', max_length=32),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
