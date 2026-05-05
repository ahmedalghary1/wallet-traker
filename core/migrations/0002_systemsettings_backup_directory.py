from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="backup_directory",
            field=models.CharField(
                blank=True,
                max_length=500,
                verbose_name="مسار حفظ النسخ الاحتياطية",
            ),
        ),
    ]
