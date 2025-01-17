# Generated by Django 4.2.8 on 2024-07-16 02:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sss', '0021_alter_catalogue_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Proxy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_path', models.CharField(max_length=255)),
                ('proxy_url', models.CharField(max_length=255)),
                ('basic_auth_enabled', models.BooleanField(default=False)),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Proxy',
                'verbose_name_plural': 'Proxies',
                'ordering': ['request_path'],
            },
        ),
    ]
