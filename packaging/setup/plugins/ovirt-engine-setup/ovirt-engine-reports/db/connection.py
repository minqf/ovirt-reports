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


import gettext


from otopi import constants as otopicons
from otopi import plugin
from otopi import transaction
from otopi import util


from ovirt_engine_setup.engine_common \
    import constants as oengcommcons
from ovirt_engine_setup.engine_common import database


from ovirt_engine_setup.reports import constants as oreportscons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-engine-reports')


@util.export
class Plugin(plugin.PluginBase):
    """Connection plugin."""

    class DBTransaction(transaction.TransactionElement):
        """yum transaction element."""

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _("Reports database Transaction")

        def prepare(self):
            pass

        def abort(self):
            connection = self._parent.environment[
                oreportscons.DBEnv.CONNECTION
            ]
            if connection is not None:
                connection.rollback()
                self._parent.environment[oreportscons.DBEnv.CONNECTION] = None

        def commit(self):
            connection = self._parent.environment[
                oreportscons.DBEnv.CONNECTION
            ]
            if connection is not None:
                connection.commit()

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
            self.DBTransaction(self)
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        name=oreportscons.Stages.DB_CONNECTION_CUSTOMIZATION,
        condition=lambda self: self.environment[oreportscons.CoreEnv.ENABLE],
        before=(
            oengcommcons.Stages.DB_OWNERS_CONNECTIONS_CUSTOMIZED,
        ),
        after=(
            oengcommcons.Stages.DIALOG_TITLES_S_DATABASE,
        ),
    )
    def _customization(self):
        dbovirtutils = database.OvirtUtils(
            plugin=self,
            dbenvkeys=oreportscons.Const.REPORTS_DB_ENV_KEYS,
        )
        dbovirtutils.getCredentials(
            name='Reports',
            queryprefix='OVESETUP_REPORTS_DB_',
            defaultdbenvkeys=oreportscons.Const.DEFAULT_REPORTS_DB_ENV_KEYS,
            show_create_msg=True,
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        condition=lambda self: self.environment[oreportscons.CoreEnv.ENABLE],
        before=(
            oengcommcons.Stages.DIALOG_TITLES_E_DATABASE,
        ),
        after=(
            oengcommcons.Stages.DIALOG_TITLES_S_DATABASE,
            oengcommcons.Stages.DB_OWNERS_CONNECTIONS_CUSTOMIZED,
        ),
    )
    def _dwh_customization(self):
        database.OvirtUtils(
            plugin=self,
            dbenvkeys=oreportscons.Const.DWH_DB_ENV_KEYS,
        ).getCredentials(
            name='DWH',
            queryprefix='OVESETUP_DWH_DB_',
            defaultdbenvkeys=oreportscons.Const.DEFAULT_DWH_DB_ENV_KEYS,
            show_create_msg=False,
            credsfile=oreportscons.FileLocations.DWH_SERVICE_CONFIG_DATABASE,
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        name=oreportscons.Stages.DB_CONNECTION_AVAILABLE,
        condition=lambda self: self.environment[oreportscons.CoreEnv.ENABLE],
        after=(
            oreportscons.Stages.DB_SCHEMA,
        ),
    )
    def _connection(self):
        self.environment[
            oreportscons.DBEnv.STATEMENT
        ] = database.Statement(
            environment=self.environment,
            dbenvkeys=oreportscons.Const.REPORTS_DB_ENV_KEYS,
        )
        # must be here as we do not have database at validation
        self.environment[
            oreportscons.DBEnv.CONNECTION
        ] = self.environment[oreportscons.DBEnv.STATEMENT].connect()


# vim: expandtab tabstop=4 shiftwidth=4
