import os
import random
import subprocess
from pathlib import Path

from sitekick.utils import hostname, ip_address


def install_script(mode='daily'):
    """Make the script run daily by setting the cron."""
    # Get the path to the script:
    script_path = Path(__file__).parent.parent / 'domains-to-sitekick.py'
    # Get the path to the cron file:
    cron_path = Path('/etc/cron.d/domains-to-sitekick')
    text = None
    if mode == 'daily':
        # Write the cron file. Set the time between 3 and 4 AM, by selecting a random minute, based on the hostname:
        random.seed(hostname + ip_address + 'cron')
        minute = random.randint(0, 59)
        text = "# Run the domains-to-sitekick script daily at a random minute between 3 and 4 AM.\n" \
               f"{minute} 3 * * * root python3 {script_path}\n"
    elif mode == 'debug':
        # Get command to execute and POST the result every 5 minutes for debugging
        text = "# Debug the domains-to-sitekick script every 5 minutes.\n" \
               f"*/5 * * * * root python3 {script_path} debug\n"
    if not text:
        print(f"Could not generate cron file for mode {mode}")
        return
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
