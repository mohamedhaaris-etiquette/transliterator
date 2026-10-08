from django.db import migrations


TABLE_NAME = "subscriptions_usersubscription"
LEGACY_COLUMNS = {
    "payment_status": "varchar(20)",
    "purchase_time": "datetime(6)",
    "remaining_usage": "int unsigned",
    "used_hours": "double",
}


def _get_existing_columns(schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, TABLE_NAME
            )
        }


def make_legacy_columns_nullable(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "mysql":
        return

    existing_columns = _get_existing_columns(schema_editor)
    with connection.cursor() as cursor:
        for name, sql_type in LEGACY_COLUMNS.items():
            if name in existing_columns:
                cursor.execute(
                    f"ALTER TABLE `{TABLE_NAME}` "
                    f"MODIFY COLUMN `{name}` {sql_type} NULL DEFAULT NULL"
                )


def restore_legacy_columns_not_null(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "mysql":
        return

    existing_columns = _get_existing_columns(schema_editor)
    fallback_values = {
        "payment_status": "''",
        "purchase_time": "`started_at`",
        "remaining_usage": "0",
        "used_hours": "0",
    }
    with connection.cursor() as cursor:
        for name, sql_type in LEGACY_COLUMNS.items():
            if name not in existing_columns:
                continue
            cursor.execute(
                f"UPDATE `{TABLE_NAME}` SET `{name}` = "
                f"{fallback_values[name]} WHERE `{name}` IS NULL"
            )
            cursor.execute(
                f"ALTER TABLE `{TABLE_NAME}` "
                f"MODIFY COLUMN `{name}` {sql_type} NOT NULL"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            make_legacy_columns_nullable,
            restore_legacy_columns_not_null,
        ),
    ]