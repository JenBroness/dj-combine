from django.db.models.base import ModelBase, Model
from django.db.migrations.state import ModelState
from django.utils import six


class Rename:
    def __init__(self, **kwargs):
        #kwargs: {newname(str) : {model(Model) : oldname(str)...}...}
        models_with_renames = set([])
        reduce_this =[ model for changes in kwargs.values() for model in changes.keys() ]
        for model in reduce_this:
            if not isinstance(model, ModelBase):
                raise Exception("Not a model")
            models_with_renames.add(model)
        self._by_model = { model: {} for model in models_with_renames }
        for newname, submapping in kwargs.items():
            for model, oldname in submapping.items():
                self._by_model[model][model._meta.get_field(oldname)] = newname
        self._by_fieldname = { newname:{ model:model._meta.get_field(oldname)
                                  for model, oldname in changes.items() }
                              for newname, changes in kwargs.items() }

    # to do: make serializable, make sqlfuncs operate on serialized info
    def deconstruct(self):
        return { newname: [(donor._meta.app_label, donor._meta.model_name, field.name) for donor, field in remap.items()]
                 for newname, remap in self._by_fieldname.items() }

    def old_name(self, contributor_model, newname):
        try:
            return self._by_fieldname[newname][contributor_model].name
        except KeyError:
            return None

    def new_name(self, contributor_model, oldname):
        try:
            return self._by_model[contributor_model][contributor_model._meta.get_field(oldname)]
        except KeyError:
            return None


class CombineOptions:
    def __init__(self, donors, renames):
        self.donors = tuple([(donor._meta.app_label, donor._meta.model_name) for donor in donors])
        self.renames = Rename(**renames)


class CombinedModelViewBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(CombinedModelViewBase, cls).__new__
        if Model in bases:
            combiner = attrs.pop('Combiner', None)
            if combiner is None: #Will be None, if model class is being reconstructed via ModelState.render()
                new_class = super_new(cls, name, bases, attrs)
            else:
                # TODO: ensure that combiner's attrs are of correct types (check deeply)
                combiner = CombineOptions(combiner.donors, combiner.renames)

                #TODO: disallow ManyToMany fields
                #TODO: disallow explicit PK field, add our own
                #TODO: Is [Model].Meta.db_table necessary or does Django generate it automatically even for unmanaged models?
                #TODO: disallow use of abstract parent models
                #TODO: disallow weird Meta options that don't make sense

                attrs['Meta'].managed = False
                new_class = super_new(cls, name, bases, attrs)
                new_class._combiner = combiner
                # TODO: disallow saves, deletes, mass updates and deletes by wrapping the manager
            return new_class
        return super_new(cls, name, bases, attrs)


class CombinedModelView(six.with_metaclass(CombinedModelViewBase)):
    #utility funcs may go here
    pass