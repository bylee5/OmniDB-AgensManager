from django.http import HttpResponse
from django.template import loader
from django.http import JsonResponse
from django.core import serializers
from django.shortcuts import redirect
from datetime import datetime
from math import ceil
import json
from os import listdir
from os.path import isfile, join, isdir
from OmniDB import settings
import importlib
from configparser import ConfigParser
from itertools import chain

#loading python plugins
plugins = {}
plugins_folders = listdir('OmniDB_app/static/plugins')
for plugin_folder in plugins_folders:
    plugin_name = ''
    plugin_version = ''
    if isfile(join('OmniDB_app/static/plugins',plugin_folder,'plugin.conf')):
        conf_exists = True
    else:
        conf_exists = False
    if isfile(join('OmniDB_app/static/plugins',plugin_folder,'plugin.js')):
        js_exists = True
    else:
        js_exists = False
    if isfile(join('OmniDB_app/static/plugins',plugin_folder,'plugin.py')):
        py_exists = True
    else:
        py_exists = False
    #if is directory, try to import plugin.py inside it
    if isdir(join('OmniDB_app/static/plugins',plugin_folder)):
        try:
            parser = ConfigParser()
            with open(join('OmniDB_app/static/plugins',plugin_folder,'plugin.conf')) as lines:
                lines = chain(("[top]",), lines)
                parser.read_file(lines)
                plugin_name = parser.get('top', 'name')
                plugin_version = parser.get('top', 'version')

            plugins[plugin_name] = {
                'module'         : importlib.import_module('OmniDB_app.static.plugins.{0}.plugin'.format(plugin_folder)),
                'folder'         : plugin_folder,
                'name'           : plugin_name,
                'version'        : plugin_version,
                'conf_exists'    : conf_exists,
                'js_exists'      : js_exists,
                'py_exists'      : py_exists,
                'javascript_file': '/static/plugins/{0}/plugin.js'.format(plugin_folder),
                'plugin_folder'  : '/static/plugins/{0}/'.format(plugin_folder)
            }
        except Exception as exc:
            plugins[plugin_name] = {
                'module'         : None,
                'folder'         : plugin_folder,
                'name'           : plugin_name,
                'version'        : plugin_version,
                'conf_exists'    : conf_exists,
                'js_exists'      : js_exists,
                'py_exists'      : py_exists,
                'javascript_file': '/static/plugins/{0}/plugin.js'.format(plugin_folder),
                'plugin_folder'  : '/static/plugins/{0}/'.format(plugin_folder)
            }

#loading javascript plugins
def get_plugins(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')

    json_object = json.loads(request.POST.get('data', None))
    plugin_list = []
    for key, plugin in plugins.items():
        plugin_list.append({ 'name': plugin['name'], 'file': plugin['javascript_file'], 'folder': plugin['plugin_folder']})

    v_return['v_data'] = plugin_list

    return JsonResponse(v_return)

#loading javascript plugins
def list_plugins(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')

    json_object = json.loads(request.POST.get('data', None))
    plugin_list = []
    for key, plugin in plugins.items():
        if plugin['conf_exists']:
            conf_html = '<img title="File exists" src="/static/OmniDB_app/images/select.png">'
        else:
            conf_html = '<img title="File not found" src="/static/OmniDB_app/images/tab_close.png">'
        if plugin['js_exists']:
            js_html = '<img title="File exists" src="/static/OmniDB_app/images/select.png">'
        else:
            js_html = '<img title="File not found" src="/static/OmniDB_app/images/tab_close.png">'
        if plugin['py_exists']:
            py_html = '<img title="File exists" src="/static/OmniDB_app/images/select.png">'
        else:
            py_html = '<img title="File not found" src="/static/OmniDB_app/images/tab_close.png">'
        if plugin['conf_exists'] and plugin['js_exists'] and plugin['py_exists']:
            plugin_enabled = '<img title="File exists" src="/static/OmniDB_app/images/select.png">'
        else:
            plugin_enabled = '<img title="File not found" src="/static/OmniDB_app/images/tab_close.png">'

        plugin_list.append([plugin['folder'],plugin['name'],plugin['version'],conf_html,js_html,py_html, plugin_enabled])


    v_return['v_data'] = plugin_list

    return JsonResponse(v_return)

def exec_plugin_function(request):

    v_return = {}
    v_return['v_data'] = ''
    v_return['v_error'] = False
    v_return['v_error_id'] = -1

    #Invalid session
    if not request.session.get('omnidb_session'):
        v_return['v_error'] = True
        v_return['v_error_id'] = 1
        return JsonResponse(v_return)

    v_session = request.session.get('omnidb_session')

    json_object = json.loads(request.POST.get('data', None))
    p_plugin_name = json_object['p_plugin_name']
    p_function_name = json_object['p_function_name']
    p_data = json_object['p_data']
    p_check_database_connection = json_object['p_check_database_connection']
    p_database_index = json_object['p_database_index']
    p_tab_id = json_object['p_tab_id']

    try:
        v_database = v_session.v_tab_connections[p_tab_id]
    except:
        v_database = None

    #Check database prompt timeout
    if p_check_database_connection and p_database_index:
        v_timeout = v_session.DatabaseReachPasswordTimeout(int(p_database_index))
        if v_timeout['timeout']:
            v_return['v_data'] = {'password_timeout': True, 'message': v_timeout['message'] }
            v_return['v_error'] = True
            return JsonResponse(v_return)

    v_return['v_data'] = getattr(plugins[p_plugin_name]['module'], p_function_name)(v_database,p_data)

    return JsonResponse(v_return)
