# Generated by Django 5.0.3 on 2024-03-23 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='description',
            field=models.TextField(default='let the games begin'),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='status',
            field=models.CharField(default='open', max_length=50),
        ),
    ]
