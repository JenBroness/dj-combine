from django.db import migrations
import combine.operations as combine_operations


class Migration(migrations.Migration):

    dependencies = [
        ('example_models', '0002_pet'),
    ]

    operations = [
        combine_operations.CreateCombinedView('Pet',
                                              [
                                                  ('example_models', 'cat'),
                                                  ('example_models', 'dog')
                                              ],
                                              {
                                                  'volume': [
                                                      ('example_models', 'cat', 'meow_volume'),
                                                      ('example_models', 'dog', 'bark_volume')
                                                  ],
                                                  'coat': [
                                                      ('example_models', 'cat', 'coat_type'),
                                                      ('example_models', 'dog', 'coat_description')
                                                  ]
                                              },
                                              {}) #hints
    ]
