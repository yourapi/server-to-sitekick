import argparse
from importlib import import_module
from pathlib import Path
from sitekick.send import send_domains
from sitekick.test_providers import test_modules
from sitekick.install import install_script
from sitekick import config

parser = argparse.ArgumentParser(
    prog='domains-to-sitekick',
    description='Domains to Sitekick commandline interface',
    epilog='For more information, see https://github.com/yourapi/server-to-sitekick#readme')
parser.add_argument('command', action='store', nargs='?', default='send', help='Command to execute',
                    choices=['send', 'install', 'test'])
parser.add_argument('args', action='store', nargs='*', help='Arguments for the specified command')
parser.add_argument('--version', action='version', version='%(prog)s 0.1')
parser.add_argument('--config-path', default=config.CONFIG_PATH, 
                    help=f'Path to configuration directory (default: {config.CONFIG_PATH})')
parser.add_argument('--queue-path', default=config.QUEUE_PATH,
                    help=f'Path to queue directory (default: {config.QUEUE_PATH})')
parser.add_argument('--sitekick-url', default=config.SITEKICK_PUSH_URL,
                    help=f'Sitekick push URL (default: {config.SITEKICK_PUSH_URL})')
parser.add_argument('--enable-autoupdate', action='store_true', default=config.ENABLE_AUTOUPDATE,
                    help='Enable automatic updates (default: disabled)')
gdpr_group = parser.add_mutually_exclusive_group()
gdpr_group.add_argument('--gdpr-compliant', dest='gdpr_compliant', action='store_true',
                        help='Enable GDPR compliant behavior (default: disabled)')
gdpr_group.add_argument('--no-gdpr-compliant', dest='gdpr_compliant', action='store_false',
                        help='Disable GDPR compliant behavior')
parser.add_argument('--gdpr-psk', default=config.GDPR_PSK,
                    help='Pre-shared key used for GDPR HMAC (default: configured value)')
system_info_group = parser.add_mutually_exclusive_group()
system_info_group.add_argument('--system-info', dest='system_info', action='store_true',
                               help='Enable system info collection (default: enabled)')
system_info_group.add_argument('--no-system-info', dest='system_info', action='store_false',
                               help='Disable system info collection')
parser.set_defaults(system_info=config.SYSTEM_INFO)
parser.set_defaults(gdpr_compliant=config.GDPR_COMPLIANT)


def send(*args):
    """Send the domains to the Sitekick server."""
    send_domains(*args)

def test(*args):
    """Test the specified provider to see if it is suitable for the local server."""
    test_modules(*args)

def install(*args):
    """Make the send-domains-to-sitekick script regularly executable, by setting the cron."""
    install_script()

def execute(args):
    """Execute the specified command."""
    config.CONFIG_PATH = args.config_path
    config.QUEUE_PATH = args.queue_path
    config.SITEKICK_PUSH_URL = args.sitekick_url
    config.ENABLE_AUTOUPDATE = args.enable_autoupdate
    config.SYSTEM_INFO = args.system_info
    config.GDPR_COMPLIANT = args.gdpr_compliant
    config.GDPR_PSK = args.gdpr_psk
    exec(f"{args.command}(*{args.args})")