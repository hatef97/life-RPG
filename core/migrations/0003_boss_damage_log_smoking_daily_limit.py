import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_randomeventtemplate_shopitem_weeklybosstemplate_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='smokinglog',
            name='daily_limit',
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='weeklybosstemplate',
            name='category_damage_map',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name='BossDamageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('damage', models.PositiveIntegerField()),
                ('source', models.CharField(max_length=60)),
                ('source_name', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('boss_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='damage_logs', to='core.weeklybossinstance')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boss_damage_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
