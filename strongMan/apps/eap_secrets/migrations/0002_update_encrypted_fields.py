from django.db import migrations

def migrate_encrypted_fields(apps, schema_editor):
    for obj in apps.get_model("eap_secrets", "Secret").objects.all():
        obj.password = obj.password
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('eap_secrets', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_encrypted_fields),
    ]
