
import subprocess

# The command and its arguments as a list
command = ["ls", "-l"]
command = 'plesk bin domain --info sitekick.eu'.split()
command = 'plesk ext wp-toolkit --info -main-domain-id 1 -path /httpdocs -format raw'.split()

# In Python 3.6, you use stdout=PIPE to capture the output
result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# The output is in bytes, so you must decode it to a string
output_string = result.stdout.decode('utf-8')

# Get the output as a list of lines, removing any empty lines
output_lines = [line for line in output_string.splitlines() if line]

# f-strings are available in Python 3.6
print("Command executed with exit code: {}".format(result.returncode))
print("--- Output Lines ---")
for line in output_lines:
    print(line)
