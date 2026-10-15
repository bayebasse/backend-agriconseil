from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cultures", "0008_referencerendement_collectee_le_and_more")]

    operations = [
        migrations.AddField(
            model_name="referencerendement",
            name="extraction_preuves",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddConstraint(
            model_name="referencerendement",
            constraint=models.UniqueConstraint(
                condition=~models.Q(source_url=""),
                fields=("culture", "source_url"),
                name="unique_reference_url_par_culture",
            ),
        ),
    ]
