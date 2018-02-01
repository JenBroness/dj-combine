import re
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from django.test import TestCase as DjTestCase
from example_models import models
from . import sqlfuncs

INDENT_TWICE = sqlfuncs.INDENT2 + sqlfuncs.INDENT7

MATCH_SOME_MOCK_NAME = "<(Magic)?Mock name='{}' id='\d+'>"

class SqlFuncsTestCase(TestCase):

    def test_field_and_rename(self):
        field = Mock()
        column = 'column'
        field.column = column
        donor_model = Mock()

        empty_renames = {}
        half_empty_renames = {column:{}}
        full_renames = MagicMock()

        self.assertEquals(sqlfuncs.field_and_rename(field, donor_model, empty_renames),
                          column)
        self.assertEquals(sqlfuncs.field_and_rename(field, donor_model, half_empty_renames),
                          column)
        self.assertEquals(sqlfuncs.field_and_rename(field, donor_model, full_renames),
                          sqlfuncs.X_AS_Y.format(x=str(full_renames[column][donor_model]), y=column))
        pass

    def test_fields_and_renames(self):
        view_model = Mock(name='view_model')
        view_model._meta = Mock(name='view_model_meta')
        donor_model = Mock(name='donor_model')
        renames = MagicMock(name='renames')

        view_model._meta.fields = []
        self.assertEquals(sqlfuncs.fields_and_renames(view_model, donor_model, renames), '\n')

        view_model._meta.fields = [view_model._meta.pk]
        self.assertEquals(sqlfuncs.fields_and_renames(view_model, donor_model, renames), '\n')

        field_objs = []
        for letter in ['a', 'b', 'c']:
            field_mock = Mock()
            field_mock.column = letter
            field_objs.append(field_mock)

        mock_name = MATCH_SOME_MOCK_NAME.format(re.escape('renames.__getitem__().__getitem__()'))

        view_model._meta.fields = field_objs
        test_regex = ",\n" + INDENT_TWICE + sqlfuncs.X_AS_Y.format(x=mock_name, y='a') + \
                     ",\n" + INDENT_TWICE + sqlfuncs.X_AS_Y.format(x=mock_name, y='b') + \
                     ",\n" + INDENT_TWICE + sqlfuncs.X_AS_Y.format(x=mock_name, y='c')
        self.assertTrue(re.match(test_regex, sqlfuncs.fields_and_renames(view_model, donor_model, renames)))



class AppWorksTestCase(DjTestCase):
    def setUp(self):
        models.Pet
        pass

    def test_app_exists(self):
        pass
