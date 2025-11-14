# Generated manually on 2025-11-14

from django.db import migrations


def normalize_tariff_codes(apps, schema_editor):
    """
    Normalize tariff codes by stripping whitespace and converting to lowercase.
    This ensures compatibility with the level property in the Tariff model.
    """
    Tariff = apps.get_model("admin_panel", "Tariff")

    updated_count = 0
    for tariff in Tariff.objects.all():
        original_code = tariff.code
        if original_code:
            normalized_code = original_code.strip().lower()
            if normalized_code != original_code:
                tariff.code = normalized_code
                tariff.save(update_fields=["code"])
                updated_count += 1
                print(f"Normalized tariff code: '{original_code}' -> '{normalized_code}'")

    if updated_count > 0:
        print(f"Total tariff codes normalized: {updated_count}")
    else:
        print("No tariff codes needed normalization")


def reverse_normalize_tariff_codes(apps, schema_editor):
    """
    Reverse migration - no operation needed as we don't store original codes.
    Manual intervention required if rollback is necessary.
    """
    print("Warning: This migration cannot be automatically reversed. "
          "Original tariff codes were not preserved.")


class Migration(migrations.Migration):

    dependencies = [
        ("admin_panel", "0008_subscription_is_trial"),
    ]

    operations = [
        migrations.RunPython(
            normalize_tariff_codes,
            reverse_normalize_tariff_codes
        ),
    ]
