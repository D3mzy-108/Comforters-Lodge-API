import django.db.models.deletion
from django.db import migrations, models

# Existing hymns are moved into this default hymnal so no data is lost.
# Rename it later from the admin if you like.
DEFAULT_HYMNAL_NAME = "C&S Hymnal"
DEFAULT_HYMNAL_COLOR = "#cebda6"


def backfill_default_hymnal(apps, schema_editor):
    Hymnal = apps.get_model("lodge", "Hymnal")
    Hymn = apps.get_model("lodge", "Hymn")
    if Hymn.objects.exists():
        hymnal, _ = Hymnal.objects.get_or_create(
            name=DEFAULT_HYMNAL_NAME,
            defaults={"color_code": DEFAULT_HYMNAL_COLOR},
        )
        Hymn.objects.filter(hymnal__isnull=True).update(hymnal=hymnal)


def noop_reverse(apps, schema_editor):
    # On reverse we simply drop the FK column (handled by the schema ops);
    # the default hymnal row is left in place harmlessly.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lodge", "0007_prayercategory_alter_prayer_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Hymnal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Name of the hymnal / songbook", max_length=255, unique=True)),
                ("color_code", models.CharField(blank=True, help_text="Accent colour for the hymnal", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        # 1) Add the FK as nullable so existing rows remain valid.
        migrations.AddField(
            model_name="hymn",
            name="hymnal",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="hymns",
                to="lodge.hymnal",
                help_text="The hymnal this hymn belongs to",
            ),
        ),
        # 2) Backfill every existing hymn into the default hymnal.
        migrations.RunPython(backfill_default_hymnal, noop_reverse),
        # 3) Now enforce NOT NULL.
        migrations.AlterField(
            model_name="hymn",
            name="hymnal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="hymns",
                to="lodge.hymnal",
                help_text="The hymnal this hymn belongs to",
            ),
        ),
        # 4) Numbering is now unique *per hymnal*, not globally.
        migrations.RemoveConstraint(
            model_name="hymn",
            name="unique_hymn_number",
        ),
        migrations.AddConstraint(
            model_name="hymn",
            constraint=models.UniqueConstraint(
                fields=["hymnal", "hymn_number"],
                name="unique_hymn_number_per_hymnal",
            ),
        ),
    ]
