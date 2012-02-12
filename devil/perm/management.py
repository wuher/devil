#  -*- coding: utf-8 -*-
# management.py ---
#
# Created: Fri Dec 23 08:29:13 2011 (+0200)
# Author: Janne Kuuskeri
#


import types
from django.db.models import signals
from devil.resource import Resource


PERM_APP_NAME = 'devil'


def _split_mod_var_names(resource_name):
    """ Return (module_name, class_name) pair from given string. """
    try:
        dot_index = resource_name.rindex('.')
    except ValueError:
        # no dot found
        return '', resource_name
    return resource_name[:dot_index], resource_name[dot_index+1:]

def _get_var_from_string(item):
    """ Get resource variable. """
    modname, varname = _split_mod_var_names(item)
    if modname:
        mod = __import__(modname, globals(), locals(), [varname], -1)
        return getattr(mod, varname)
    else:
        return globals(varname)

def _is_resource_obj(item):
    return isinstance(item, Resource)

def _is_string(item):
    return type(item) == types.StringType

def _instantiate_resource(item):
    try:
        res = item()
    except TypeError:
        return None
    else:
        return res if _is_resource_obj(res) else None

def _handle_string(item):
    var = _get_var_from_string(item)
    resource_obj = _instantiate_resource(item)
    if resource_obj:
        return [resource_obj]
    else:
        return _handle_list(var)

def _handle_resource_setting(item):
    if _is_resource_obj(item):
        # print 'object:', item
        return [item]
    elif _is_string(item):
        # print 'string:', item
        return _handle_string(item)
    else:
        # todo
        print '###', item

def _handle_list(reclist):
    """ Return list of resources that have access_controller defined. """
    ret = []
    for item in reclist:
        recs = _handle_resource_setting(item)
        ret += [resource for resource in recs if resource.access_controller]
    return ret

def get_resources():
    from django.conf import settings
    try:
        acl_resources = settings.ACL_RESOURCES
    except AttributeError:
        # ACL_RESOURCES is not specified in settings
        return []
    else:
        return _handle_list(acl_resources)

def _ensure_content_type():
    """ Add the bulldog content type to the database if it's missing. """
    from django.contrib.contenttypes.models import ContentType
    try:
        row = ContentType.objects.get(app_label=PERM_APP_NAME)
    except ContentType.DoesNotExist:
        row = ContentType(name=PERM_APP_NAME, app_label=PERM_APP_NAME, model=PERM_APP_NAME)
        row.save()
    return row.id

def _get_permission_description(permission_name):
    """ Generate a descriptive string based on the permission name.

    For example: 'resource_Order_get'  ->  'Can GET order'

    todo: add support for the resource name to have underscores
    """

    parts = permission_name.split('_')
    parts.pop(0)
    method = parts.pop()
    resource = ('_'.join(parts)).lower()
    return 'Can %s %s' % (method.upper(), resource)

def _populate_permissions(resources, content_type_id):
    """ Add all missing permissions to the database. """
    from django.contrib.auth.models import Permission
    # read the whole auth_permission table into memory
    db_perms = [perm.codename for perm in Permission.objects.all()]

    for resource in resources:
        # get all resource's permissions that are not already in db
        perms = [perm for perm in resource.access_controller.get_perm_names(resource) if perm not in db_perms]
        for perm in perms:
            Permission(
                name=_get_permission_description(perm),
                content_type_id=content_type_id,
                codename=perm).save()

def _update_db(resources):
    """ Add the content type and all permissions if they are missing. """
    content_type_id = _ensure_content_type()
    _populate_permissions(resources, content_type_id)

def update_permissions(app, created_models, verbosity=2, **kwargs):
    resources = get_resources()
    _update_db(resources)

signals.post_syncdb.connect(update_permissions)


#
# management.py ends here
