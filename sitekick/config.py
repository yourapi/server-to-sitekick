CONFIG_PATH = '/etc/server-to-sitekick'
# This token ONLY has access to two end points: /assets/templates/connectors/*plesk*/content and
# /client/administration/queues/*plesk*
QUEUE_PATH = '/tmp/sitekick/domains'
SITEKICK_PUSH_URL = 'https://eu.sitekick.online/sitekick/public/post/servers'
SITEKICK_DEBUG_URL = 'https://eu.sitekick.online/debug'
ENABLE_AUTOUPDATE = False
SYSTEM_INFO = True
GDPR_COMPLIANT = False
GDPR_PSK="your-very-secret-psk-for-hmac"
PLESK_BINARY = '/usr/sbin/plesk'