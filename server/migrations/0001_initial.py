# Generated by Django 4.2.13 on 2024-06-06 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset', models.CharField(max_length=50)),
                ('entry_price', models.IntegerField()),
                ('exit_price', models.IntegerField()),
                ('risk_price', models.IntegerField()),
                ('target_price', models.IntegerField()),
            ],
        ),
    ]
