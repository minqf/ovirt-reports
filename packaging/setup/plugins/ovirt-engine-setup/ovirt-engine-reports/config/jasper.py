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


import gettext
import os

from otopi import plugin
from otopi import util

from ovirt_engine_setup import constants as osetupcons
from ovirt_engine_setup.reports import constants as oreportscons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-engine-reports')


@util.export
class Plugin(plugin.PluginBase):

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            osetupcons.CoreEnv.DEVELOPER_MODE
        ],
    )
    def _validation(self):
        if not os.path.exists(
            self.environment[
                oreportscons.ConfigEnv.JASPER_HOME
            ]
        ):
            raise RuntimeError(
                _(
                    'Cannot find jasper reports server at {path}'
                ).format(
                    path=self.environment[
                        oreportscons.ConfigEnv.JASPER_HOME
                    ]
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
