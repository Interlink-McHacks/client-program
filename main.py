import errno
import random
import socket
import subprocess
import sys
from rich.console import Console
import getpass
from control_plane_access import ControlPlaneAccessInstance
import dbm

db = dbm.open('interlink_persist', 'c')
WG_IP = '10.45.106.10'
RETRY_MAX = 20
console = Console()
ctrl_plane = ControlPlaneAccessInstance()


def get_wg_port(retry=0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = random.randint(20_000, 60_000)
    try:
        s.bind((WG_IP, port))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE and retry < RETRY_MAX:
            return get_wg_port(retry=retry + 1)
        else:
            sys.exit(-1)
    s.close()
    return port


def activate_tunnel(target_port):
    wg_port = get_wg_port()
    output = subprocess.Popen(['websockify', f'{WG_IP}:{wg_port}', f'127.0.0.1:{target_port}'])
    console.print(f'Starting Interlink listening on localhost:{target_port} through Wireguard on port {wg_port}', style='bold green')
    while True:
        continue


def entry():
    console.print("INTERLINK - Access the world!", style='bold blue')
    host_id = db.get('host_id').decode()
    host_secret = db.get('host_secret').decode()
    ctrl_plane.host_id = host_id
    ctrl_plane.host_secret = host_secret
    ctrl_plane.tenant_id = db.get('tenant_id').decode() or '61ec73a88d868f0bfc5a3ce6'

    if not host_id or not host_secret:
        console.print('Please authenticate with credentials to join control plane', style='italic green')
        name = input(f'Hostname ({socket.gethostname()}): ')
        name = socket.gethostname() if not name else name
        tenant_id = input('Tenant ID: ')
        join_token = getpass.getpass('Join Token: ')
        data = ctrl_plane.enroll(tenant_id, join_token, name, WG_IP)['data']
        db['host_id'] = data['hostID']
        db['host_secret'] = data['secret']
        db['hostname'] = name
        db['tenant_id'] = tenant_id
        ctrl_plane.host_id = data['hostID']
        ctrl_plane.host_secret = data['secret']
    else:
        # print(host_secret, host_id)
        console.print(f'Authenticated with host id [u]{host_id}[/u]', style='bold green')
    db.close()

    console.log('Starting daemon', style='italic purple')
    cmd_tuns = ctrl_plane.contact_cmd()
    console.log('Control Plane Response:', cmd_tuns)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    entry()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
