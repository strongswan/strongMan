from django.db import migrations


def migrate_encrypted_field(model):
    for obj in model.objects.all():
        obj.der_container = obj.der_container
        obj.save()


def migrate_encrypted_fields(apps, schema_editor):
    migrate_encrypted_field(apps.get_model("certificates", "PrivateKey"))
    migrate_encrypted_field(apps.get_model("certificates", "Certificate"))
    migrate_encrypted_field(apps.get_model("certificates", "UserCertificate"))
    migrate_encrypted_field(apps.get_model("certificates", "ViciCertificate"))


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_encrypted_fields),
    ]
