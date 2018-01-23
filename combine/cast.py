from itertools import chain

class ModelMultiAlias(object):
    def __init__(self, *args):
        self._submodels = args
        self._filter_proxies = { m: {} for m in args }
        managers = [ m._default_manager for m in args ]
        manager = MultiModelManager(managers, self)
        self._default_manager = manager
        self.objects = manager

class MultiModelManager(object):
    def __init(self, managers, cast_model):
        self._managers = managers
        self._cast_model = cast_model

    def __getattr__(self, *args, **kwargs):
        return get_multi_queryset_callable_or_values(self._managers, self._model_)

def get_multi_queryset_callable_or_values(attr_owners, multi_model, *args, **kwargs):
    objs = [ object.__getattribute__(owner, *args, **kwargs) for owner in attr_owners ]
    are_callable = [ hasattr(obj, '__call__') for obj in objs ]
    if all(x for x in are_callable):
        return MultiQuerySetCallable(objs, multi_model)
    if any(x for x in are_callable):
        raise Exception("Some items are callable and others are not")
    return tuple(objs)

class MultiQuerySet(object):
    def __init__(self, querysets, multi_model):
        self._querysets = querysets
        self._multi_model = multi_model
    def __iter__(self):
        return chain(*(self._querysets))
    def __getattr__(self, *args, **kwargs):
        return get_multi_queryset_callable_or_values(self._querysets, self._multi_model, *args, **kwargs)

class MultiQuerySetCallable(object):
    def __init__(selfself, sub_callables, multi_model):
        self.sub_callables = sub_callables
        self.multi_model = multi_model
    def __call__(self, *args, **kwargs):
        iterables = []
        for s in self.sub_callables:
            # filter_proxies = self.multi_model._filter_proxy_terms[s.im_self.model]
            # new_kwargs = { (do filter proxy stuff) }
            queryset_or_single_item = s(*args, **kwargs)
            if hasattr(queryset_or_single_item, '__iter__'):
                new_iterable = queryset_or_single_item
            else:
                # This should actually throw an exception if multiple models have each single items,
                # to make the behavior like a base django model
                new_iterable = [queryset_or_single_item]
            iterables.append(new_iterable)
        return MultiQuerySet(iterables, self.model_union)