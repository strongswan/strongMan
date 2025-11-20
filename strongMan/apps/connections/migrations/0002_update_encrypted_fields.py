from django.db import migrations

def migrate_encrypted_fields(apps, schema_editor):
    for obj in apps.get_model("connections", "Secret").objects.all():
        obj.data = obj.data
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('connections', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_encrypted_fields),
    ]
