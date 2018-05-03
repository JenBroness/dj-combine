# dj-combine

This project is a work in progress, and is tested only with Postgres and Python 3 as of 5/3/2018!

For the creation of views that merge two or more models together, by aliasing column names and UNIONING thus-aliased rows
together. These views are defined in Python in the same way as Django models, and can be queried in limited ways through 
the Django ORM.

You can create such a view by inheriting from the CombinedModelView class in addition to Model. Add a Combiner class definition
within your CombinedModelView body to define the merge in terms of 'donors' (the models to merge) and 'renames' (a mapping of 
field names from the original models to aliases representing new, combined fields).

CombinedModelViews are always unmanaged.

Here's a quick example of the functionality from the 'example_models' app. (Subject to change.)

```
FEW_CHARS = 15
MANY_CHARS = 45
QUIET = 2
LOUD = 6
LOUDEST = 10

class Cat(models.Model):
    name = models.CharField(max_length=FEW_CHARS)
    meow_volume = models.PositiveSmallIntegerField(default=QUIET)
    breed = models.CharField(max_length=FEW_CHARS)
    coat_type = models.CharField(max_length=FEW_CHARS)


class Dog(models.Model):
    name = models.CharField(max_length=FEW_CHARS)
    bark_volume = models.PositiveSmallIntegerField(default=LOUD)
    breed = models.CharField(max_length=FEW_CHARS)
    coat_description = models.CharField(max_length=MANY_CHARS) #Will be grouped in the view with 'coat_type' from Cat
    wags_per_second = models.FloatField(default=3.0)


class Pet(CombinedModelView, models.Model):
    id = models.TextField(primary_key=True) #populated automatically as "<model_table>.<model_pk>"
    name = models.CharField(max_length=FEW_CHARS)
    volume = models.PositiveSmallIntegerField()
    breed = models.CharField(max_length=FEW_CHARS)
    coat = models.CharField(max_length=MANY_CHARS)

    class Meta:
        db_table='example_models_pets'

    class Combiner:
        donors = (Cat, Dog)
        renames = {
            'volume': {Cat: 'meow_volume', Dog: 'bark_volume'},
            'coat': {Cat: 'coat_type', Dog: 'coat_description'}
        }
```