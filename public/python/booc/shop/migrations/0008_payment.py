# Generated by Django 5.1.4 on 2025-04-29 22:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_alter_order_customer_address_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('address', models.TextField()),
                ('contact', models.CharField(max_length=50)),
                ('receipt', models.ImageField(help_text='Upload proof of payment (receipt image)', upload_to='receipts/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(help_text='The order this payment belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='shop.order')),
            ],
        ),
    ]
