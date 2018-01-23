from django.db import models
from combine.base import CombinedModelView
from copy import copy
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation

# class ContributorLink(models.Model):
#     creation=models.ForeignKey(Creation)
#     creation_content_type = models.ForeignKey(ContentType)
#     contributor = models.ForeignKey(Person)
#     contributor_content_type = models.ForeignKey(ContentType)
#
#
# class Person(models.Model):
#     fname = models.CharField(max_length=15)
#     lname = models.CharField(max_length=15)
#     creations = models.ManyToManyField(Creation, through='ContributorLink', related_name='contributors')
#
#
# class Author(Person):
#     genre = models.CharField(max_length=20)
#
#
# class Artist(Person):
#     style = models.CharField(max_length=20)
#
#
# class Creation(models.Model):
#     title = models.CharField(max_length=150)
#
#
# class Artwork(Creation):
#     contributors = models.ManyToManyField(Artist)
#
#
# class Story(Creation):
#     contributors = models.ManyToManyField(Author)
#
#
# class Paper(Creation):
#     contributors = models.ManyToManyField(Author)
#
#
# class CrossCollaboration(Creation):
#     pass
## General collaboration is a proxy that can refer to Story, Artwork, Paper, CrossCollaboration

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
    id = models.TextField(primary_key=True)
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

class ExtraPet(CombinedModelView, models.Model):
    id = models.TextField(primary_key=True)
    name = models.CharField(max_length=FEW_CHARS)

    class Meta:
        db_table='example_models_extrapets'

    class Combiner:
        donors = (Cat, Dog)
        renames = {}