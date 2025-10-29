# Initial migration - mark existing schema as migrated

from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        # Database schema already exists from previous setup
        # This migration establishes the baseline for future migrations
        migrations.RunSQL(
            sql=migrations.RunSQL.noop,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
