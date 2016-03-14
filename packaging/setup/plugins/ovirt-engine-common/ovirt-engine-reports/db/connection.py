#
# ovirt-engine-setup -- ovirt engine setup
# Copyright (C) 2013-2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""Connection plugin."""


import configparser
import gettext
import io
import os

from otopi import constants as otopicons
from otopi import plugin
from otopi import util

from ovirt_engine import configfile

from ovirt_engine_setup import constants as osetupcons
from ovirt_engine_setup.engine_common import database
from ovirt_engine_setup.reports import constants as oreportscons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-engine-reports')


@util.export
class Plugin(plugin.PluginBase):
    """Connection plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
    )
    def _boot(self):
        self.environment[
            otopicons.CoreEnv.LOG_FILTER_KEYS
        ].append(
            oreportscons.DBEnv.PASSWORD
        )
        self.environment[
            otopicons.CoreEnv.LOG_FILTER_KEYS
        ].append(
            oreportscons.DWHDBEnv.PASSWORD
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            oreportscons.DBEnv.HOST,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.PORT,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.SECURED,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.SECURED_HOST_VALIDATION,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.USER,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.PASSWORD,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.DATABASE,
            None
        )
        self.environment.setdefault(
            oreportscons.DBEnv.DUMPER,
            oreportscons.Defaults.DEFAULT_DB_DUMPER
        )
        self.environment.setdefault(
            oreportscons.DBEnv.FILTER,
            oreportscons.Defaults.DEFAULT_DB_FILTER
        )
        self.environment.setdefault(
            oreportscons.DBEnv.RESTORE_JOBS,
            oreportscons.Defaults.DEFAULT_DB_RESTORE_JOBS
        )

        self.environment[oreportscons.DBEnv.CONNECTION] = None
        self.environment[oreportscons.DBEnv.STATEMENT] = None
        self.environment[oreportscons.DBEnv.NEW_DATABASE] = True

        self.environment.setdefault(
            oreportscons.DWHDBEnv.HOST,
            None
        )
        self.environment.setdefault(
            oreportscons.DWHDBEnv.PORT,
            None
        )
        self.environment.setdefault(
            oreportscons.DWHDBEnv.SECURED,
            None
        )
        self.environment.setdefault(
            oreportscons.DWHDBEnv.SECURED_HOST_VALIDATION,
            None
        )
        self.environment.setdefault(
            oreportscons.DWHDBEnv.USER,
            None
        )
        self.environment.setdefault(
            oreportscons.DWHDBEnv.PASSWORD,
            None
        )
        self.environment.setdefault(
            oreportscons.DWHDBEnv.DATABASE,
            None
        )

        self.environment[oreportscons.DWHDBEnv.CONNECTION] = None
        self.environment[oreportscons.DWHDBEnv.STATEMENT] = None
        self.environment[oreportscons.DWHDBEnv.NEW_DATABASE] = True

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _commands(self):
        dbovirtutils = database.OvirtUtils(
            plugin=self,
            dbenvkeys=oreportscons.Const.REPORTS_DB_ENV_KEYS,
        )
        dbovirtutils.detectCommands()

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        name=oreportscons.Stages.DB_CONNECTION_SETUP,
    )
    def _setup(self):
        p = None
        if os.path.exists(
            os.path.join(
                self.environment[oreportscons.ConfigEnv.JASPER_HOME],
                (
                    oreportscons.FileLocations.
                    LEGACY_OVIRT_ENGINE_REPORTS_BUILDOMATIC_DBPROP
                ),
            )
        ) and os.path.exists(
            self.environment[oreportscons.ConfigEnv.LEGACY_REPORTS_WAR],
        ):
            self.environment[oreportscons.CoreEnv.ENABLE] = True
            p = os.path.join(
                self.environment[oreportscons.ConfigEnv.JASPER_HOME],
                (
                    oreportscons.FileLocations.
                    LEGACY_OVIRT_ENGINE_REPORTS_BUILDOMATIC_DBPROP
                ),
            )
        elif os.path.exists(
            oreportscons.FileLocations.OVIRT_ENGINE_REPORTS_BUILDOMATIC_DBPROP
        ):
            p = (
                oreportscons.FileLocations.
                OVIRT_ENGINE_REPORTS_BUILDOMATIC_DBPROP
            )

        if (
            p is not None and
            self.environment[oreportscons.CoreEnv.ENABLE]
        ):
            config = configparser.ConfigParser()
            config.optionxform = str
            with open(p) as f:
                config.readfp(
                    io.StringIO(
                        '[default]' +
                        f.read().decode('utf-8')
                    )
                )
            dbenv = {}
            try:
                for e, k in (
                    (oreportscons.DBEnv.HOST, 'dbHost'),
                    (oreportscons.DBEnv.PORT, 'dbPort'),
                    (oreportscons.DBEnv.USER, 'dbUsername'),
                    (oreportscons.DBEnv.PASSWORD, 'dbPassword'),
                    (oreportscons.DBEnv.DATABASE, 'js.dbName'),
                ):
                    dbenv[e] = config.get('default', k)

                dbenv[
                    oreportscons.DBEnv.SECURED
                ] = dbenv[
                    oreportscons.DBEnv.SECURED_HOST_VALIDATION
                ] = False

                dbovirtutils = database.OvirtUtils(
                    plugin=self,
                    dbenvkeys=oreportscons.Const.REPORTS_DB_ENV_KEYS,
                )
                dbovirtutils.tryDatabaseConnect(dbenv)
                self.environment.update(dbenv)
                self.environment[
                    oreportscons.DBEnv.NEW_DATABASE
                ] = dbovirtutils.isNewDatabase()
            except RuntimeError as e:
                self.logger.debug(
                    'Existing credential use failed',
                    exc_info=True,
                )
                msg = _(
                    'Cannot connect to Reports database using existing '
                    'credentials: {user}@{host}:{port}'
                ).format(
                    host=dbenv[oreportscons.DBEnv.HOST],
                    port=dbenv[oreportscons.DBEnv.PORT],
                    database=dbenv[oreportscons.DBEnv.DATABASE],
                    user=dbenv[oreportscons.DBEnv.USER],
                )
                if self.environment[
                    osetupcons.CoreEnv.ACTION
                ] == osetupcons.Const.ACTION_REMOVE:
                    self.logger.warning(msg)
                else:
                    raise RuntimeError(msg)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        condition=lambda self: (
            self.environment[oreportscons.CoreEnv.ENABLE] and
            # If dwh is enabled, let it check its own stuff
            not self.environment.get(oreportscons.DWHCoreEnv.ENABLE)
        ),
    )
    def _dwh_setup(self):
        config = configfile.ConfigFile([
            oreportscons.FileLocations.SERVICE_DEFAULTS,
            oreportscons.FileLocations.SERVICE_VARS,
        ])
        if config.get('DWH_DB_PASSWORD'):
            try:
                dbenv = {}
                for e, k in (
                    (oreportscons.DWHDBEnv.HOST, 'DWH_DB_HOST'),
                    (oreportscons.DWHDBEnv.PORT, 'DWH_DB_PORT'),
                    (oreportscons.DWHDBEnv.USER, 'DWH_DB_USER'),
                    (oreportscons.DWHDBEnv.PASSWORD, 'DWH_DB_PASSWORD'),
                    (oreportscons.DWHDBEnv.DATABASE, 'DWH_DB_DATABASE'),
                ):
                    dbenv[e] = (
                        self.environment.get(e)
                        if self.environment.get(e) is not None
                        else config.get(k)
                    )
                for e, k in (
                    (oreportscons.DWHDBEnv.SECURED, 'DWH_DB_SECURED'),
                    (
                        oreportscons.DWHDBEnv.SECURED_HOST_VALIDATION,
                        'DWH_DB_SECURED_VALIDATION'
                    )
                ):
                    dbenv[e] = config.getboolean(k)

                dbovirtutils = database.OvirtUtils(
                    plugin=self,
                    dbenvkeys=oreportscons.Const.DWH_DB_ENV_KEYS,
                )
                dbovirtutils.tryDatabaseConnect(dbenv)
                self.environment.update(dbenv)
                self.environment[
                    oreportscons.DWHDBEnv.NEW_DATABASE
                ] = dbovirtutils.isNewDatabase()
            except RuntimeError as e:
                self.logger.debug(
                    'Existing credential use failed',
                    exc_info=True,
                )
                msg = _(
                    'Cannot connect to DWH database using existing '
                    'credentials: {user}@{host}:{port}'
                ).format(
                    host=dbenv[oreportscons.DWHDBEnv.HOST],
                    port=dbenv[oreportscons.DWHDBEnv.PORT],
                    database=dbenv[oreportscons.DWHDBEnv.DATABASE],
                    user=dbenv[oreportscons.DWHDBEnv.USER],
                )
                if self.environment[
                    osetupcons.CoreEnv.ACTION
                ] == osetupcons.Const.ACTION_REMOVE:
                    self.logger.warning(msg)
                else:
                    raise RuntimeError(msg)


# vim: expandtab tabstop=4 shiftwidth=4
