from django.db import migrations, models


create_view_sql = """
CREATE OR REPLACE VIEW example_models_pets AS
  SELECT concat('example_models_cat.', id::text) AS id,
         name,
         meow_volume AS volume,
         breed,
         coat_type AS coat
         FROM example_models_cat
  UNION
  SELECT concat('example_models_dog.', id::text) AS id,
         name,
         bark_volume AS volume,
         breed,
         coat_description AS coat
         FROM example_models_dog
"""

drop_view_sql = """
DROP VIEW IF EXISTS example_models_pets
"""


class Migration(migrations.Migration):

    dependencies = [
        ('example_models', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(create_view_sql, reverse_sql=drop_view_sql)
    ]
