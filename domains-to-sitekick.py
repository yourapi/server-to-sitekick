#!/usr/bin/env python3 .domains-to-sitekick.py
# -*- coding: utf-8 -*-
# File: domains-to-sitekick.py
# The shebang does not work on CentOS plesk servers. Use the following command to run the script:
# python3 domains-to-sitekick.py
"""
Entry point of server-to-sitekick: loads the configuration and executes the command.

Copyright 2025 Sitekick

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import sys
from importlib import util
from pathlib import Path

try:
    __file__
except NameError:
    __file__ = os.path.abspath('domains-to-sitekick.py')


# Now, set the python path dynamically to enable loading of modules:
current_path = str(Path(__file__).parent.absolute())
if os.getenv('PYTHONPATH'):
    python_path = os.environ['PYTHONPATH'].split(os.pathsep)
    if current_path not in python_path:
        os.environ['PYTHONPATH'] = os.pathsep.join([current_path] + python_path)
else:
    os.environ['PYTHONPATH'] = current_path

# Execute the supplied or default command. The command is executed in the commandline module, which dispatches the
# command to the relevant module/function:
from sitekick import config
from sitekick.commandline import parser, execute


def _get_config_path(argv, default_path):
    for i, arg in enumerate(argv):
        if arg == '--config-path' and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith('--config-path='):
            return arg.split('=', 1)[1]
    return default_path


def _load_config_from_path(config_path):
    """Load config overrides from the given config.py file or directory."""
    config_path = Path(config_path)
    if config_path.is_dir():
        config_dir = config_path
        config_file = config_dir / 'config.py'
    else:
        config_file = config_path
        config_dir = config_file.parent
    if not config_file.exists():
        return False
    spec = util.spec_from_file_location('sitekick_external_config', str(config_file))
    if spec is None or spec.loader is None:
        return False
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ('QUEUE_PATH', 'SITEKICK_PUSH_URL', 'SYSTEM_INFO', 'GDPR_COMPLIANT', 'GDPR_PSK'):
        if hasattr(module, name):
            setattr(config, name, getattr(module, name))
    config.CONFIG_PATH = str(config_dir)
    return True


config_path = _get_config_path(sys.argv[1:], config.CONFIG_PATH)
_load_config_from_path(config_path)
parser.set_defaults(
    config_path=config.CONFIG_PATH,
    queue_path=config.QUEUE_PATH,
    sitekick_url=config.SITEKICK_PUSH_URL,
    system_info=config.SYSTEM_INFO,
    gdpr_compliant=config.GDPR_COMPLIANT,
    gdpr_psk=config.GDPR_PSK,
)

args = parser.parse_args()

# Now execute the command:
execute(args)
