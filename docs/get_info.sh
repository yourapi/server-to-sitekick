# Get the present domains and instances
plesk bin site --list

# Get the info for a site, including the instance-id
plesk bin domain --info sitekick.eu

# Get the extended info for an instance. We would love to have json, but the generated json is not correct
# So use the raw output and parse the output ourselves.
plesk ext wp-toolkit --info -instance-id 1 -format raw  # instances not found yet
# the path is the local path specified in --WWW-Root--: /var/www/vhosts/sitekick.eu/httpdocs
plesk ext wp-toolkit --info -main-domain-id 1 -path /httpdocs -format raw

