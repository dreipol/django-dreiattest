# Generated by Django 5.1 on 2024-08-08 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dreiattest', '0005_key_driver'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='devicesession',
            new_name='dreiattest__user_id_0e3f7c_idx',
            old_fields=('user_id', 'session_id'),
        ),
    ]
