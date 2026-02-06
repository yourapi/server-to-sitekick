#!/usr/bin/env python3 .domains-to-sitekick.py
# -*- coding: utf-8 -*-
# File: domains-to-sitekick.py
# The shebang does not work on CentOS plesk servers. Use the following command to run the script:
# python3 domains-to-sitekick.py
"""
This file kickstarts the download and execution of the code from the Sitekick server.

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
import json
import os
import socket
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request

# Include the code for downloading IN this file, to have a single installable file (easy to install):
CODE_ENDPOINT = 'https://api.github.com/repos/yourapi/server-to-sitekick/releases'

try:
    __file__
except NameError:
    __file__ = os.path.abspath('domains-to-sitekick.py')


def load_code(root_path=None):
    """CHANGE THIS to loading the code from github and extracting it, comparing the timestamp of the current files to
    that of the last release. Use ONLY github for code download, for maximum transparency!"""
    if not root_path:
        root_path = Path(__file__).parent.parent
        # The root path of the server-to-sitekick code, this code is in level 1
    if '145-131-8-226' in socket.gethostname():  # Local testing preventing overwriting of local code
        return
    req = Request(CODE_ENDPOINT)
    files = json.loads(urlopen(req).read())
    for file in files:
        try:
            filename = Path(root_path, file['path'], file['name'])
            # Split the time zone; Python 3.5 has no %z parse field:
            timestamp, offset = file['_timestamp_'].split('+')
            offset = datetime.strptime(offset, '%H:%M')
            seconds = datetime.strptime(timestamp,
                                        '%Y-%m-%dT%H:%M:%S.%f').timestamp() + offset.hour * 3600 + offset.minute * 60
            if (filename.exists()
                    and filename.stat().st_mtime > seconds):
                continue
            content = urlopen(Request(file['content'])).read()
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_bytes(content)
            print('Downloaded', filename)
        except Exception as e:
            print(f"Download of {file['content']} failed with exception: {e}")
            continue


# First, get the code from the Sitekick server and refresh all code:
# load_code(Path(__file__).parent)

# Now, set the python path dynamically to enable loading of modules:
current_path = str(Path(__file__).parent.absolute())
if os.getenv('PYTHONPATH'):
    python_path = os.environ['PYTHONPATH'].split(os.pathsep)
    if current_path not in python_path:
        os.environ['PYTHONPATH'] = os.pathsep.join([current_path] + python_path)
else:
    os.environ['PYTHONPATH'] = current_path

# Now the code is bootstrapped, execute the supplied or default command. The command is executed in the commandline
# module, which dispatches the command to the relevant module/function:
from sitekick.commandline import parser, execute

# Now execute the command:
execute(parser.parse_args())
