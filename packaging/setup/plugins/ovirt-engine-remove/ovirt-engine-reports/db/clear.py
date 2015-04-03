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


"""Clear plugin."""


import gettext


from otopi import plugin
from otopi import util


from ovirt_engine_setup import constants as osetupcons
from ovirt_engine_setup import dialog
from ovirt_engine_setup.engine_common import database


from ovirt_engine_setup.reports import constants as oreportscons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-engine-reports')


@util.export
class Plugin(plugin.PluginBase):
    """Clear plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            oreportscons.RemoveEnv.REMOVE_DATABASE,
            None
        )
        self._bkpfile = None

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        after=(
            osetupcons.Stages.REMOVE_CUSTOMIZATION_COMMON,
        ),
    )
    def _customization(self):
        if self.environment[
            osetupcons.RemoveEnv.REMOVE_ALL
        ]:
            self.environment[
                oreportscons.RemoveEnv.REMOVE_DATABASE
            ] = True

        if self.environment[
            oreportscons.RemoveEnv.REMOVE_DATABASE
        ] is None:
            self.environment[
                oreportscons.RemoveEnv.REMOVE_DATABASE
            ] = dialog.queryBoolean(
                dialog=self.dialog,
                name='OVESETUP_REPORTS_REMOVE_DATABASE',
                note=_(
                    'Do you want to remove Reports DB content? All data will '
                    'be lost (@VALUES@) [@DEFAULT@]: '
                ),
                prompt=True,
                true=_('Yes'),
                false=_('No'),
                default=False,
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: (
            self.environment[oreportscons.DBEnv.PASSWORD] is not None and
            self.environment[oreportscons.RemoveEnv.REMOVE_DATABASE]
        ),
        after=(
            oreportscons.Stages.DB_CREDENTIALS_AVAILABLE,
        ),
    )
    def _misc(self):

        try:
            dbovirtutils = database.OvirtUtils(
                plugin=self,
                dbenvkeys=oreportscons.Const.REPORTS_DB_ENV_KEYS,
            )
            dbovirtutils.tryDatabaseConnect()
            self._bkpfile = dbovirtutils.backup(
                dir=self.environment[
                    oreportscons.ConfigEnv.OVIRT_ENGINE_REPORTS_DB_BACKUP_DIR
                ],
                prefix=(
                    oreportscons.Const.
                    OVIRT_ENGINE_REPORTS_DB_BACKUP_PREFIX
                ),
            )
            self.logger.info(
                _('Clearing Reports database {database}').format(
                    database=self.environment[oreportscons.DBEnv.DATABASE],
                )
            )
            dbovirtutils.clearDatabase()

        except RuntimeError as e:
            self.logger.debug('exception', exc_info=True)
            self.logger.warning(
                _(
                    'Cannot clear Reports database: {error}'
                ).format(
                    error=e,
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._bkpfile is not None,
        before=(
            osetupcons.Stages.DIALOG_TITLES_E_SUMMARY,
        ),
        after=(
            osetupcons.Stages.DIALOG_TITLES_S_SUMMARY,
        ),
    )
    def _closeup(self):
        self.dialog.note(
            text=_(
                'A backup of the Reports database is available at {path}'
            ).format(
                path=self._bkpfile
            ),
        )

# vim: expandtab tabstop=4 shiftwidth=4
