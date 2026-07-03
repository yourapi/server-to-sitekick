import os
import random
import subprocess
from importlib import import_module
from pathlib import Path
from pprint import pprint

from sitekick.utils import hostname, ip_address


def install_script():
    """Make the script run daily by setting the cron."""
    # Get the path to the script:
    script_path = Path(__file__).parent.parent / 'domains-to-sitekick.py'
    # Get the path to the cron file:
    cron_path = Path('/etc/cron.d/domains-to-sitekick')
    # Write the cron file. Set the time between 3 and 4 AM, by selecting a random minute, based on the hostname:
    random.seed(hostname + ip_address + 'cron')
    minute = random.randint(0, 59)
    text = r"# Run the domains-to-sitekick script daily at a random minute between 3 and 4 AM.\n" \
           fr"{minute} 3 * * * root python3 {script_path}\n"
    text = r"# Run the domains-to-sitekick script daily every 5 minutes.\n" \
           fr"*/5 * * * * root python3 {script_path}\n"
    if os.geteuid() == 0:
        # Current user has write rights on the cron file, write the cron file:
        cron_path.open('w').write(text)
    else:
        # This does not work guaranteed. Running sudo from shell does not work out fine...
        op = '>'
        for line in text.split('\n'):
            proc = subprocess.run(['sudo', 'echo', f'"{line}"', op, str(cron_path)], shell=True, timeout=10,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            op = '>>'
    print(f"Written cron file {cron_path}")
