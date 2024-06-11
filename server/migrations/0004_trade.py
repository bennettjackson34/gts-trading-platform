# Generated by Django 2.1.15 on 2024-06-06 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('server', '0003_delete_trade'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset', models.CharField(max_length=50)),
                ('direction', models.IntegerField()),
                ('entry_price', models.IntegerField()),
                ('exit_price', models.IntegerField()),
                ('risk_price', models.IntegerField()),
                ('target_price', models.IntegerField()),
            ],
        ),
    ]