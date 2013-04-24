#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# Copyright (C) 2013  Nexcess.net L.L.C.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""A plugin for YUM to easily exclude updates newer than a given period.
Intended to allow simple staging of updates.
"""

__title__       = 'yum-plugin-lag'
__version__     = '0.0.1'
__author__      = 'Alex Headley <aheadley@nexcess.net>'
__license__     = 'GPLv2'
__copyright__   = 'Copyright (C) 2013  Nexcess.net L.L.C.'


import logging
import time
import functools

from yum.plugins import PluginYumExit, TYPE_CORE

LOG_INFO = 2
LOG_VERBOSE = 3

requires_api_version = '2.3'
plugin_type = (TYPE_CORE,)

_YLP_SINGLETON = None

def plugin_hook(func):
    @functools.wraps(func)
    def inner_func(self, conduit):
        self._conduit = conduit
        return func(self, conduit)
    return inner_func

class YumLagPlugin(object):
    DEFAULT_EXCLUDE_NEWER_THAN  = 7
    DEFAULT_CHECK_MODE          = 'file'

    ERROR_INVALID_EXCLUDE_PERIOD    = 'exclude_newer_than must be >= 0 (value: %d)'
    ERROR_INVALID_CHECK_MODE        = 'Invalid check_mode: %s'

    TIMESTAMP_CHECK_FUNCS           = {
        'file': lambda pkg: int(pkg.returnSimple('time_file')),
        'build': lambda pkg: int(pkg.returnSimple('time_build')),
    }

    _conf = {
        'exclude_newer_than':   {},
        'check_mode':           DEFAULT_CHECK_MODE,
    }
    _conduit = None

    def __init__(self):
        self.TIMESTAMP_CHECK_FUNCS['newest'] = \
            lambda pkg: max([
                self.TIMESTAMP_CHECK_FUNCS['file'](pkg),
                self.TIMESTAMP_CHECK_FUNCS['build'](pkg)])
        self.TIMESTAMP_CHECK_FUNCS['oldest'] = \
            lambda pkg: min([
                self.TIMESTAMP_CHECK_FUNCS['file'](pkg),
                self.TIMESTAMP_CHECK_FUNCS['build'](pkg)])

    def _validate_config(self):
        for repo_id in self._conf['exclude_newer_than']:
            if self._conf['exclude_newer_than'][repo_id] < 0:
                raise PluginYumExit(self.ERROR_INVALID_EXCLUDE_PERIOD %
                    self._conf['exclude_newer_than'][repo_id])
        if self._conf['check_mode'] not in ['file', 'build', 'newest', 'oldest']:
            raise PluginYumExit(self.ERROR_INVALID_CHECK_MODE %
                self._conf['check_mode'])

    def _get_ts_check_func(self, repo_id):
        get_ts = self.TIMESTAMP_CHECK_FUNCS[self._conf['check_mode']]
        ts_cutoff = int(time.time()) - \
            (self._conf['exclude_newer_than'][repo_id] * 86400)

        check_func = lambda pkg: get_ts(pkg) > ts_cutoff

        return check_func

    @staticmethod
    def get():
        global _YLP_SINGLETON
        if _YLP_SINGLETON is None:
            _YLP_SINGLETON = YumLagPlugin()
        return _YLP_SINGLETON

    @plugin_hook
    def init_hook(self, conduit):
        conduit.registerPackageName(__title__)

        ENT = conduit.confInt('main', 'exclude_newer_than',
            default=self.DEFAULT_EXCLUDE_NEWER_THAN)
        for repo in conduit.getRepos().listEnabled():
            try:
                repo_ENT = repo.exclude_newer_than
            except AttributeError:
                repo_ENT = ENT
            self._conf['exclude_newer_than'][repo.id] = repo_ENT
            self._conduit.info(LOG_VERBOSE,
                'Set repo (%s) to exclude_newer_than=%d' % (repo.id, repo_ENT))

    @plugin_hook
    def config_hook(self, conduit):
        parser = conduit.getOptParser()
        parser.add_option('', '--exclude-newer-than',
            action='store', default=None, type='int', metavar='DAYS',
            help='Exclude updates newer than DAYS, overrides global and per-repo config value')

    @plugin_hook
    def prereposetup_hook(self, conduit):
        opts, commands = conduit.getCmdLine()
        if opts.exclude_newer_than is not None:
            for repo_id in self._conf['exclude_newer_than']:
                self._conf['exclude_newer_than'][repo_id] = opts.exclude_newer_than
            self._conduit.info(LOG_VERBOSE,
                'Set all repos to exclude_newer_than=%d' % opts.exclude_newer_than)
        self._validate_config()

    @plugin_hook
    def exclude_hook(self, conduit):
        for repo in conduit.getRepos().listEnabled():
            if repo.id in self._conf['exclude_newer_than']:
                pkg_is_too_new = self._get_ts_check_func(repo.id)
                for pkg in conduit.getPackages(repo):
                    if pkg_is_too_new(pkg):
                        conduit.delPackage(pkg)
                        conduit.info(LOG_VERBOSE,
                            ' --> %s from %s excluded (too new)' % \
                                (pkg, repo.id))

# Setup the real hooks that YUM looks for
YLP = YumLagPlugin.get()
for hook in (h for h in dir(YLP) if h.endswith('_hook') and not h.startswith('_')):
    globals()[hook] = getattr(YLP, hook)

def main():
    pass

if __name__ == '__main__':
    main()
