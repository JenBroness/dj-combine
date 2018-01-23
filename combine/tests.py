from django.test import TestCase
from example_models import models


class AppWorksTestCase(TestCase):
    def setUp(self):
        models.Pet
        pass

    def test_app_exists(self):
        pass

# class CastModelTestCase(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         for artist in [('Frida', 'Kahlo'),
#                        ('Salvador', 'Dali'),
#                        ('Pablo', 'Picasso'),
#                        ('Jackson', 'Pollock'),
#                        ('Jean-Michel', 'Basquiat'),
#                        ]:
#             models.Artist.create(fname=artist[0], lname=artist[1])
#         for author in [('Michael', 'Crichton'),
#                        ('JK', 'Rowling'),
#                        ('Stephen', 'King'),
#                        ('Toni', 'Morrison'),
#                        ('Charles', 'Dickens'),
#                        ]:
#             models.Author.create(fname=author[0], lname=author[1])
#
