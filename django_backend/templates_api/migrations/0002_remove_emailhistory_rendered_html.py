from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("templates_api", "0001_emailhistory"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="emailhistory",
            name="rendered_html",
        ),
    ]
