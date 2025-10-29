# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0002_add_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE admin_panel_channel
                ADD COLUMN IF NOT EXISTS title_emoji VARCHAR(10) NOT NULL DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE admin_panel_channel
                DROP COLUMN IF EXISTS title_emoji;
            """,
        ),
    ]
