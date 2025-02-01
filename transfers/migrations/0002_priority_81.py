from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("transfers", "0001_initial")]

    operations = [
        migrations.AddField(model_name="transfer", name="priority", field=models.IntegerField(default=0)),
    ]
