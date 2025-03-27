# Generated by Django 5.0 on 2025-03-26 08:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('resources', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_resources', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resource',
            name='uploaded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_resources', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resource',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='resources.resourcecategory'),
        ),
        migrations.AddField(
            model_name='resourcecomment',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='resources.resource'),
        ),
        migrations.AddField(
            model_name='resourcecomment',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resource_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resourcerating',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='resources.resource', verbose_name='资源'),
        ),
        migrations.AddField(
            model_name='resourcerating',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='评分用户'),
        ),
        migrations.AlterUniqueTogether(
            name='resourcerating',
            unique_together={('resource', 'user')},
        ),
    ]
