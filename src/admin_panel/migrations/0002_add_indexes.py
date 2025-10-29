# Manual migration to add indexes to existing tables

from django.db import migrations, models


def create_indexes(apps, schema_editor):
    """Create indexes if they don't exist"""
    db_alias = schema_editor.connection.alias

    indexes_sql = [
        # Flow table indexes
        'CREATE INDEX IF NOT EXISTS "admin_panel_flow_id_42070c_idx" ON "admin_panel_post" ("flow_id", "created_at" DESC);',
        # Post table indexes
        'CREATE INDEX IF NOT EXISTS "admin_panel_source__60f68d_idx" ON "admin_panel_post" ("source_id");',
        'CREATE INDEX IF NOT EXISTS "admin_panel_status_31ae21_idx" ON "admin_panel_post" ("status", "scheduled_time");',
    ]

    with schema_editor.connection.cursor() as cursor:
        for sql in indexes_sql:
            cursor.execute(sql)


def drop_indexes(apps, schema_editor):
    """Drop the created indexes"""
    indexes_sql = [
        'DROP INDEX IF EXISTS "admin_panel_flow_id_42070c_idx";',
        'DROP INDEX IF EXISTS "admin_panel_source__60f68d_idx";',
        'DROP INDEX IF EXISTS "admin_panel_status_31ae21_idx";',
    ]

    with schema_editor.connection.cursor() as cursor:
        for sql in indexes_sql:
            cursor.execute(sql)


class Migration(migrations.Migration):
    dependencies = [
        ("admin_panel", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_indexes, drop_indexes),
    ]
