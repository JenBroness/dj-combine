import re, six
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from django.db.models.base import ModelBase, Model
from django.db.models.fields import TextField
from django.test import TestCase as DjTestCase
from example_models import models
from . import sqlfuncs
from .base import Rename, CombinedModelView, CombinedModelViewBase

INDENT_TWICE = sqlfuncs.INDENT2 + sqlfuncs.INDENT7

MATCH_SOME_MOCK_NAME = "<(Magic)?Mock name='{}' id='\d+'>"
MOCK_APP_LABEL = 'mock_app_label'
PATCH_MODEL_BASE_RETURN_VALUE = 'patched ModelBase.__new__ return value'

class FieldMock(Mock):
    def __eq__(self, other):
        return other._is_field_mock and self.column == other.column

    def __hash__(self):
        return hash('Field' + self.column)

    def __init__(self, *args, **kwargs):
        super(FieldMock, self).__init__(*args, **kwargs)
        self.column = kwargs['name']
        self.is_field_mock = True
        self.name = kwargs['name']

def field_mocks(names):
    return [ FieldMock(name=name) for name in names ]

def mock_model(tblname, fieldname_list, app_label=None):
    donor = Mock(name=tblname)
    donor._meta = Mock()
    donor._meta.db_table = tblname
    donor._meta.pk = Mock()
    donor._meta.pk.name = 'id'
    donor._meta.fields = field_mocks(fieldname_list)
    donor._meta.app_label = app_label or MOCK_APP_LABEL
    donor._meta.model_name = tblname
    return donor

class TestMockSetup(TestCase):
    def test_field_mock(self):
        mock1 = FieldMock(name='1')
        mock2 = FieldMock(name='1')
        self.assertEqual(mock1, mock2)

class TestSqlFuncs(TestCase):

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

        # this is just what MagicMock faked array access looks like when printed
        mock_name = MATCH_SOME_MOCK_NAME.format(re.escape('renames.__getitem__().__getitem__()'))

        view_model._meta.fields = field_mocks(['a', 'b', 'c'])
        test_regex = ",\n" + INDENT_TWICE + sqlfuncs.X_AS_Y.format(x=mock_name, y='a') + \
                     ",\n" + INDENT_TWICE + sqlfuncs.X_AS_Y.format(x=mock_name, y='b') + \
                     ",\n" + INDENT_TWICE + sqlfuncs.X_AS_Y.format(x=mock_name, y='c')
        self.assertTrue(re.match(test_regex, sqlfuncs.fields_and_renames(view_model, donor_model, renames)))

    def test_construction_sql(self):
        view_model = mock_model('view', ['a', 'b', 'c'])
        donor1 = mock_model('donor1', ['a', 'b', 'c'])
        donor2 = mock_model('donor2', ['a', 'b', 'c'])
        donor3 = mock_model('donor3', ['a', 'b', 'c'])
        test_sql = """
        CREATE OR REPLACE VIEW view AS
        SELECT concat('donor1.', id::text) AS id,
               a,
               b,
               c
               FROM donor1
        UNION
        SELECT concat('donor2.', id::text) AS id,
               a,
               b,
               c
               FROM donor2
        UNION
        SELECT concat('donor3.', id::text) AS id,
               a,
               b,
               c
               FROM donor3
        """
        gen_sql = sqlfuncs.construction_sql(view_model, [donor1, donor2, donor3], {})
        self.assertEqual(test_sql.split(), gen_sql.split())

    def test_destruction_sql(self):
        view_model = mock_model('view', ['a', 'b', 'c'])
        test_sql = """
        DROP VIEW IF EXISTS view
        """
        gen_sql = sqlfuncs.destruction_sql(view_model)
        self.assertEqual(test_sql.split(), gen_sql.split())


class TestCombinedViewOperationPrivateMethods(TestCase):

    def test_get_reconstructed_view_model(self):
        pass

    def test_get_reconstructed_donors(self):
        pass

    def test_get_reconstructed_renames(self):
        pass


class TestMakeCombinedViewsCommand(TestCase):

    def test_gather_combined_models(self):
        pass

    def test_handle_init(self):
        pass

    def test_historical_combined_models(self):
        pass

    def test_get_combined_model_additions_and_removals(self):
        pass


class TestViewTypeConstruction(TestCase):

    def setUp(self):
        def mock_get_field(oldname):
            return FieldMock(name=oldname)
        self.donor1 = mock_model('Donor1', [])
        self.donor2 = mock_model('Donor2', [])
        self.donor3 = mock_model('Donor3', [], app_label='different_app')
        for donor in self.donor1, self.donor2, self.donor3:
            donor._meta.get_field = mock_get_field
        self.base_constructor_kwargs = {
            'newname1': {self.donor1: 'd1_oldname1', self.donor2: 'd2_oldname1', self.donor3: 'd3_oldname1'},
            'newname2': {self.donor2: 'd2_oldname2', self.donor3: 'd3_oldname2'},
            'newname3': {self.donor3: 'd3_oldname3'}
        }

    def test_rename_constructor(self):
        constructor_kwargs = (
            {},
            {'newname':{}},
            {'newname':{self.donor1:'oldname'}},
            self.base_constructor_kwargs
        )
        by_model_attrs = (
            {},
            {},
            {self.donor1:{FieldMock(name='oldname'):'newname'}},
            {self.donor1:{FieldMock(name='d1_oldname1'):'newname1'},
             self.donor2:{FieldMock(name='d2_oldname1'):'newname1',
                          FieldMock(name='d2_oldname2'):'newname2'},
             self.donor3:{FieldMock(name='d3_oldname1'):'newname1',
                          FieldMock(name='d3_oldname2'):'newname2',
                          FieldMock(name='d3_oldname3'):'newname3'}
             }
        )
        by_fieldname_attrs = (
            {},
            {'newname':{}},
            {'newname':{self.donor1:FieldMock(name='oldname')}},
            {'newname1':{self.donor1:FieldMock(name='d1_oldname1'),
                         self.donor2:FieldMock(name='d2_oldname1'),
                         self.donor3:FieldMock(name='d3_oldname1')},
             'newname2':{self.donor2:FieldMock(name='d2_oldname2'),
                         self.donor3:FieldMock(name='d3_oldname2')},
             'newname3':{self.donor3:FieldMock(name='d3_oldname3')}
             }
        )
        for (kwargs, test_by_model, test_by_fieldname) in zip(constructor_kwargs, by_model_attrs, by_fieldname_attrs):
            rename = Rename(**kwargs)

            self.assertEqual(rename._by_model, test_by_model)
            self.assertEqual(rename._by_fieldname, test_by_fieldname)


    def test_rename_deconstruct(self):
        oldMaxDiff = self.maxDiff
        self.maxDiff = None
        rename = Rename(**self.base_constructor_kwargs)
        test_deconstruct = {'newname1': [(MOCK_APP_LABEL, 'Donor1', 'd1_oldname1'),
                                         (MOCK_APP_LABEL, 'Donor2', 'd2_oldname1'),
                                         ('different_app', 'Donor3', 'd3_oldname1')
                                         ],
                            'newname2': [(MOCK_APP_LABEL, 'Donor2', 'd2_oldname2'),
                                         ('different_app', 'Donor3', 'd3_oldname2')
                                         ],
                            'newname3': [('different_app', 'Donor3', 'd3_oldname3')
                                         ]
                            }
        gen_deconstruct = rename.deconstruct()
        self.assertEqual(test_deconstruct, gen_deconstruct)
        self.maxDiff = oldMaxDiff

    def test_construct_as_non_model(self):
        class NonModel(six.with_metaclass(CombinedModelViewBase)):
            pass
        with self.assertRaises(AttributeError):
            NonModel._combiner

    def test_without_providing_combiner(self):
        with patch.object(ModelBase, '__new__', return_value=PATCH_MODEL_BASE_RETURN_VALUE):
            class NewModelView(CombinedModelView, Model):
                field1 = TextField(primary_key=True)
            self.assertEqual(NewModelView, PATCH_MODEL_BASE_RETURN_VALUE)

    def test_creates_combiner(self):
        with patch.object(ModelBase, '__new__', return_value=Mock(name='FakeClass')) as model_base_new:
            class NewModelView(CombinedModelView, Model):
                field1 = TextField(primary_key=True)
                class Combiner:
                    donors = ()
                    renames = {}
            self.assertTrue(hasattr(NewModelView, '_combiner'))


    def test_illegal_configurations(self):
        pass


class AppWorksTestCase(DjTestCase):
    def setUp(self):
        models.Pet
        pass

    def test_app_exists(self):
        pass
