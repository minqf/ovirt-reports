#
# ovirt-engine-setup -- ovirt engine setup
# Copyright (C) 2016 Red Hat, Inc.
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


from otopi import plugin
from otopi import util

from ovirt_engine import java

from ovirt_engine_setup.reports import constants as oreportscons


@util.export
class Plugin(plugin.PluginBase):

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            oreportscons.ConfigEnv.JAVA_HOME,
            None
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: (
            self.environment[
                oreportscons.ConfigEnv.JAVA_HOME
            ] is None and
            self.environment[
                oreportscons.CoreEnv.ENABLE
            ]
        ),
    )
    def _validation(self):
        self.environment[
            oreportscons.ConfigEnv.JAVA_HOME
        ] = java.Java(component='reports').getJavaHome()


# vim: expandtab tabstop=4 shiftwidth=4
