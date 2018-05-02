from django.db import models
from combine.base import CombinedModelView
from django.contrib.auth.models import User

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

class UserActivity(models.Model):
    time_posted = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)


class Replyable(UserActivity):
    forum = models.CharField(max_length=10)
    views = models.PositiveIntegerField()
    content = models.TextField()


class Post(Replyable):
    pass


class Comment(Replyable):
    in_response_to = models.ForeignKey(Replyable, related_name='subcomments')

class React(UserActivity):
    REACT_CHOICES = (
        ('LK', 'Like'),
        ('MZ', 'Amaze'),
        ('SD', 'Sad'),
        ('LV', 'Love'),
        ('NG', 'Angry'),
    )
    in_response_to = models.ForeignKey(Replyable, related_name='reacts')
    reaction = models.CharField(max_length=2, choices=REACT_CHOICES)

class ReplyView(CombinedModelView, models.Model):
    id = models.TextField(primary_key=True)
    in_response_to = models.ForeignKey(Replyable)
    content = models.TextField()

    class Combiner:
        donors = (Comment, React)
        renames = {
            'content': {Comment: 'content', React: 'reaction'}
        }

    class Meta:
        db_table='example_models_replyviews'
