import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cultures", "0009_reference_extraction_preuves_and_url_unique")]

    operations = [
        migrations.AddField(
            model_name="referencerendement",
            name="document_fichier",
            field=models.FileField(
                blank=True,
                upload_to="agronomy_documents/%Y/%m/",
                validators=[django.core.validators.FileExtensionValidator(["pdf"])],
            ),
        ),
    ]
