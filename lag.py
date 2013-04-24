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


import time

from yum.plugins import PluginYumExit, TYPE_CORE
from yum import config as yum_config

LOG_INFO = 2    # this level is regular visibility
LOG_VERBOSE = 3 # this is only visible with -v

requires_api_version = '2.3'
plugin_type = (TYPE_CORE,)
# reference to the YumLagPlugin singleton
_YLP_SINGLETON = None


class YumLagPlugin(object):
    DEFAULT_EXCLUDE_NEWER_THAN  = 7
    MAX_EXCLUDE_NEWER_THAN      = 365
    DEFAULT_CHECK_MODE          = 'file'

    ERROR_INVALID_EXCLUDE_PERIOD    = 'exclude_newer_than must be >= 0 (value: %d)'
    ERROR_INVALID_CHECK_MODE        = 'Invalid check_mode: %s'

    TIMESTAMP_CHECK_FUNCS           = {
        # get the RPM file timestamp (mtime on the repo host)
        'file': lambda pkg: int(pkg.returnSimple('time_file')),
        # get the RPM BuildDate tag
        'build': lambda pkg: int(pkg.returnSimple('time_build')),
    }

    _is_update = False

    def __init__(self):
        """We can't do much here besides add the other check modes since this
        object is created before we have a conduit which we need to do
        anything useful
        """
        self.TIMESTAMP_CHECK_FUNCS['newest'] = \
            lambda pkg: max(
                self.TIMESTAMP_CHECK_FUNCS['file'](pkg),
                self.TIMESTAMP_CHECK_FUNCS['build'](pkg))
        self.TIMESTAMP_CHECK_FUNCS['oldest'] = \
            lambda pkg: min(
                self.TIMESTAMP_CHECK_FUNCS['file'](pkg),
                self.TIMESTAMP_CHECK_FUNCS['build'](pkg))

    def _get_ts_check_func(self, conduit, repo):
        """Build the timestamp checking function based on the exclude_newer_than
        option for the repo and global check_mode. The constructed function
        will return True if the package is too new and False otherwise
        """
        conduit.info(LOG_VERBOSE,
            'Building ts_check func with ENT=%d and check_mode=%s for repo: %s' % \
                (repo.exclude_newer_than, repo.check_mode, repo.id))

        get_ts = self.TIMESTAMP_CHECK_FUNCS[repo.check_mode]
        ts_cutoff = int(time.time()) - (repo.exclude_newer_than * 86400)

        check_func = lambda pkg: get_ts(pkg) > ts_cutoff
        return check_func

    def constrain_ENT(self, value):
        return max(0, min(value, self.MAX_EXCLUDE_NEWER_THAN))

    @staticmethod
    def get():
        """Singleton access method, because everything should have OO patterns
        shoe-horned in.
        """
        global _YLP_SINGLETON
        if _YLP_SINGLETON is None:
            _YLP_SINGLETON = YumLagPlugin()
        return _YLP_SINGLETON

    def config_hook(self, conduit):
        """Add any CLI options we need
        """
        yum_config.RepoConf.check_mode = yum_config.SelectionOption(
            default=conduit.confString('main', 'check_mode',
                self.DEFAULT_CHECK_MODE),
            allowed=self.TIMESTAMP_CHECK_FUNCS.keys())

        yum_config.RepoConf.exclude_newer_than = yum_config.IntOption(
            default=self.constrain_ENT(conduit.confInt('main', 'exclude_newer_than',
                self.DEFAULT_EXCLUDE_NEWER_THAN)),
            range_min=0, range_max=self.MAX_EXCLUDE_NEWER_THAN)

        parser = conduit.getOptParser()
        parser.add_option('', '--exclude-newer-than',
            action='store', default=None, type='int', metavar='DAYS',
            help='Exclude updates newer than DAYS, overrides global and per-repo config value')

    def prereposetup_hook(self, conduit):
        """Apply the CLI options (if given) to the config and validate the
        resulting config
        """
        opts, commands = conduit.getCmdLine()
        if opts.exclude_newer_than is not None:
            ENT = self.constrain_ENT(opts.exclude_newer_than)
            for repo in conduit.getRepos().listEnabled():
                repo.exclude_newer_than = ENT
                conduit.info(LOG_VERBOSE,
                    'Set repos to exclude_newer_than=%d' % opts.exclude_newer_than)

        if 'update' in commands or 'upgrade' in commands:
            self._is_update = True

    def exclude_hook(self, conduit):
        """Meat of the plugin. Walk through each package by repo, check if the
        proposed update is too new and remove it if so. Nothing is done if
        not using the 'update' or 'upgrade' commands
        """
        if self._is_update:
            for repo in conduit.getRepos().listEnabled():
                if repo.exclude_newer_than > 0:
                    pkg_is_too_new = self._get_ts_check_func(conduit, repo)
                    for pkg in conduit.getPackages(repo):
                        if pkg_is_too_new(pkg):
                            conduit.delPackage(pkg)
                            conduit.info(LOG_VERBOSE,
                                ' --> %s from %s excluded (too new)' % \
                                    (pkg, repo.id))

# Setup the real hooks that YUM looks for
YLP = YumLagPlugin.get()
for hook in (h for h in dir(YLP) \
        if h.endswith('_hook') and not h.startswith('_')):
    globals()[hook] = getattr(YLP, hook)
