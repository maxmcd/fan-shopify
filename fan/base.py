
class BaseView(object):
    """
        Base class for all views -- for now, these are just marker classes.
    """

    __abstract__ = True

    @classmethod
    def _viewFunc(cls, method):
        def _func(**kwargs):
            if not rutil.safeAccess(config.CONFIG, 'WEB', 'DISABLE_REQUEST_LOGGING'):
                from web import analytics
                analytics.logProperties(
                    viewCls=cls.__name__,
                    viewMethod=method.__name__,
                )
            inst = cls()
            result = method(inst, **kwargs)
            return result
        return _func

def Route(rule, **kwargs):
    # Decorator applied to view methods which sets up a route for that method
    # Accepts all the same kwargs as Flask.add_url_rule
    # If endpoint is not provided, it is auto-generated as ClassName.methodName
    def _func(method):
        if not hasattr(method, '_routes'):
            method._routes = []
        method._routes.append((rule, kwargs))
        return method
    return _func
