import re

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def convert_objectives_to_structured(apps, schema_editor):
    WeeklyBossTemplate = apps.get_model("core", "WeeklyBossTemplate")
    for template in WeeklyBossTemplate.objects.all():
        objectives = template.objectives or []
        new_objectives = []
        for i, obj in enumerate(objectives):
            if isinstance(obj, str):
                slug = re.sub(r"[^a-z0-9]+", "_", obj.lower()).strip("_")
                slug = slug[:40] or f"obj_{i}"
                new_objectives.append(
                    {"id": slug, "label": obj, "category": None, "target": 1, "manual": True}
                )
            elif isinstance(obj, dict):
                new_objectives.append(obj)
        template.objectives = new_objectives
        template.save(update_fields=["objectives"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_boss_damage_log_smoking_daily_limit"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Remove HP-based tracking from WeeklyBossInstance
        migrations.RemoveField(model_name="weeklybossinstance", name="current_hp"),
        migrations.RemoveField(model_name="weeklybossinstance", name="max_hp"),
        # Add objective-based tracking
        migrations.AddField(
            model_name="weeklybossinstance",
            name="objective_progress",
            field=models.JSONField(default=dict, blank=True),
        ),
        # Remove damage map from template
        migrations.RemoveField(model_name="weeklybosstemplate", name="category_damage_map"),
        # Drop BossDamageLog entirely
        migrations.DeleteModel(name="BossDamageLog"),
        # Convert string objectives to structured dicts
        migrations.RunPython(convert_objectives_to_structured, migrations.RunPython.noop),
    ]
