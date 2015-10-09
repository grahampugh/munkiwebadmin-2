from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.http import Http404
#from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.conf import settings
from django import forms

from models import Packages
from catalogs.models import Catalog

import fnmatch
import json
import os

PROD_CATALOG = "production" # change this if your production catalog is different

@login_required
def index(request):
    can_view_pkgs = request.user.has_perm('pkgs.can_view_pkgs')
    can_view_manifests = request.user.has_perm('manifests.can_view_manifests')
    can_view_catalogs = request.user.has_perm('catalogs.can_view_catalogs')
    change_pkgs = request.user.has_perm('pkgs.change_pkgs')
    delete_pkgs = request.user.has_perm('pkgs.delete_pkgs')
    if request.method == 'GET':
        findtext = request.GET.get('findtext')
        all_catalog_items = Packages.detail(findtext)
    else:
        all_catalog_items = Packages.detail()
    catalog_list = Catalog.list()
    catalog_name = 'none'
    if PROD_CATALOG in catalog_list:
        catalog_name = PROD_CATALOG
    elif 'testing' in catalog_list:
        catalog_name = 'testing'
    return render_to_response('pkgs/index.html',
                              {'user': request.user,
                               'all_catalog_items': all_catalog_items,
                               'catalog_list': catalog_list,
                               'catalog_name': catalog_name,
                               'findtext': findtext,
                               'can_view_pkgs': can_view_pkgs,
                               'can_view_manifests': can_view_manifests,
                               'can_view_catalogs': can_view_catalogs,
                               'change_pkgs': change_pkgs,
                               'delete_pkgs': delete_pkgs,
                               'page': 'pkgs'})

@login_required
def confirm(request):
    can_view_pkgs = request.user.has_perm('pkgs.can_view_pkgs')
    can_view_manifests = request.user.has_perm('manifests.can_view_manifests')
    can_view_catalogs = request.user.has_perm('catalogs.can_view_catalogs')
    change_pkgs = request.user.has_perm('pkgs.change_pkgs')
    delete_pkgs = request.user.has_perm('pkgs.delete_pkgs')
    if request.method == 'POST': # If the form has been submitted...
        dest_catalog = request.POST.get('dest_catalog')
        items_to_move = request.POST.getlist('items_to_move[]')
        confirm_move = request.POST.get('move')
        confirm_add = request.POST.get('add')
        confirm_remove = request.POST.get('remove')
        confirm_delete = request.POST.get('delete')
        tuple(items_to_move)
        for n,pkg in enumerate(items_to_move):
            pkg = pkg.split('___')
            items_to_move[n] = pkg
        c = {'user': request.user,
             'dest_catalog': dest_catalog,
             'items_to_move': items_to_move,
             'confirm_move': confirm_move,
             'confirm_add': confirm_add,
             'confirm_remove': confirm_remove,
             'confirm_delete': confirm_delete,
             'can_view_pkgs': can_view_pkgs,
             'can_view_manifests': can_view_manifests,
             'can_view_catalogs': can_view_catalogs,
             'change_pkgs': change_pkgs,
             'delete_pkgs': delete_pkgs,
             'page': 'pkgs'}
        return render_to_response('pkgs/confirm.html', c)
    else:
        return HttpResponse("No form submitted.\n")

@login_required
def done(request):
    can_view_pkgs = request.user.has_perm('pkgs.can_view_pkgs')
    can_view_manifests = request.user.has_perm('manifests.can_view_manifests')
    can_view_catalogs = request.user.has_perm('catalogs.can_view_catalogs')
    change_pkgs = request.user.has_perm('pkgs.change_pkgs')
    delete_pkgs = request.user.has_perm('pkgs.delete_pkgs')
    if request.method == 'POST': # If the form has been submitted...
        final_items_to_move = request.POST.getlist('final_items_to_move[]')
        confirm_move = request.POST.get('confirm_move')
        confirm_add = request.POST.get('confirm_add')
        confirm_remove = request.POST.get('confirm_remove')
        new_dest_catalog = request.POST.get('new_dest_catalog')
        if new_dest_catalog:
            new_dest_catalog = new_dest_catalog.lower()
        tuple(final_items_to_move)
        for n,pkg in enumerate(final_items_to_move):
            pkg = pkg.split('___')
            final_items_to_move[n] = pkg
        if confirm_remove:
            for pkg_name, pkg_version, pkg_orig in final_items_to_move:
                if pkg_orig != 'no-catalog':
                    Packages.remove(pkg_name, pkg_version, pkg_orig)
        elif confirm_add:
            for pkg_name, pkg_version, pkg_orig, pkg_catalog in final_items_to_move:
                if pkg_orig == 'no-catalog':
                    if pkg_catalog == 'set-new' and new_dest_catalog:
                        Packages.move(pkg_name, pkg_version, new_dest_catalog)
                    elif pkg_catalog != 'set-new':
                        Packages.move(pkg_name, pkg_version, pkg_catalog)
                else:
                    if pkg_catalog == 'set-new' and new_dest_catalog:
                        Packages.add(pkg_name, pkg_version, pkg_orig, new_dest_catalog)
                    elif pkg_catalog != 'set-new':
                        Packages.add(pkg_name, pkg_version, pkg_orig, pkg_catalog)
        else:
            for pkg_name, pkg_version, pkg_catalog in final_items_to_move:
                if new_dest_catalog:
                    pkg_catalog = new_dest_catalog
                elif pkg_catalog != 'set-new':
                    Packages.move(pkg_name, pkg_version, pkg_catalog)
        Packages.makecatalogs()
        context = {'user': request.user,
                   'final_items_to_move': final_items_to_move,
                   'confirm_move': confirm_move,
                   'confirm_add': confirm_add,
                   'confirm_remove': confirm_remove,
                   'can_view_pkgs': can_view_pkgs,
                   'can_view_manifests': can_view_manifests,
                   'can_view_catalogs': can_view_catalogs,
                   'change_pkgs': change_pkgs,
                   'delete_pkgs': delete_pkgs,
                   'done': 'Done',
                   'page': 'pkgs'}
        return render_to_response('pkgs/done.html', context)
    else:
        return HttpResponse("No form submitted.\n")

@login_required
def deleted(request):
    can_view_pkgs = request.user.has_perm('pkgs.can_view_pkgs')
    can_view_manifests = request.user.has_perm('manifests.can_view_manifests')
    can_view_catalogs = request.user.has_perm('catalogs.can_view_catalogs')
    change_pkgs = request.user.has_perm('pkgs.change_pkgs')
    delete_pkgs = request.user.has_perm('pkgs.delete_pkgs')
    if request.method == 'POST': # If the form has been submitted...
        final_items_to_delete = request.POST.getlist('final_items_to_delete[]')
        tuple(final_items_to_delete)
        deleted_packages = []
        for n,pkg in enumerate(final_items_to_delete):
            pkg = pkg.split('___')
            final_items_to_delete[n] = pkg
        for pkg_name, pkg_version, pkg_location in final_items_to_delete:
            Packages.delete_pkgs(pkg_name, pkg_version)
            deleted_packages.append(pkg_location)
        Packages.makecatalogs()
        context = {'user': request.user,
                   'final_items_to_delete': final_items_to_delete,
                   'deleted_packages': deleted_packages,
                   'deleted': 'Deleted',
                   'can_view_pkgs': can_view_pkgs,
                   'can_view_manifests': can_view_manifests,
                   'can_view_catalogs': can_view_catalogs,
                   'change_pkgs': change_pkgs,
                   'delete_pkgs': delete_pkgs,
                   'page': 'pkgs'}
        return render_to_response('pkgs/deleted.html', context)
    else:
        return HttpResponse("No form submitted.\n")

@login_required
def test(request):
    add_pkgs = request.user.has_perm('pkgs.add_pkgs')
    can_view_manifests = request.user.has_perm('manifests.can_view_manifests')
    can_view_catalogs = request.user.has_perm('catalogs.can_view_catalogs')
    context =  {'user': request.user,
                'page': 'pkgs',
                'can_view_manifests': can_view_manifests,
                'can_view_catalogs': can_view_catalogs,
                'add_pkgs': add_pkgs}
    return render_to_response('pkgs/test.html', context)