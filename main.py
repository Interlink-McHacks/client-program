import socket
import subprocess
import sys
from rich.console import Console
import getpass
from control_plane_access import ControlPlaneAccessInstance
import dbm
import time
import signal


db = dbm.open('interlink_persist', 'c')
WG_IP = '10.45.106.10'
RETRY_MAX = 20
console = Console()
ctrl_plane = ControlPlaneAccessInstance()


def activate_tunnel(target_port, wg_port):
    output = subprocess.Popen(['websockify', f'{WG_IP}:{wg_port}', f'127.0.0.1:{target_port}'])
    console.print(f'Starting Interlink listening on localhost:{target_port} through Wireguard on port {wg_port}', style='bold green')
    return output


def entry():
    console.print("INTERLINK - Access the world!", style='bold blue')
    host_id = (db.get('host_id') or ''.encode()).decode()
    host_secret = (db.get('host_secret') or ''.encode()).decode()
    ctrl_plane.host_id = host_id
    ctrl_plane.host_secret = host_secret
    ctrl_plane.tenant_id = (db.get('tenant_id') or ''.encode()).decode()

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
    ctrl_plane.tunnels = []

    while True:
        new = ctrl_plane.contact_cmd()['tunnels']
        console.log('Updating tunnel list', style='blue')
        # console.log('Control Plane Response:', new)
        diff = ctrl_plane.diff_cmd_result_and_update(new)
        # print(diff)
        for tun in diff['add']:
            console.print(f'Creating new tunnel on local port {tun["hostConnectPort"]}', style='bold green')
            result = activate_tunnel(tun['hostConnectPort'], tun['wgListeningPort'])
            ctrl_plane.ws_processes[tun['_id']] = result
        for tun in diff['remove']:
            console.print(f'Removing old tunnel on local port {tun["hostConnectPort"]}', style='bold red')
            process = ctrl_plane.ws_processes[tun['_id']]
            process.kill()
            del ctrl_plane.ws_processes[tun['_id']]
        time.sleep(3)


def signal_handler(sig, frame):
    console.print('\nShutting down Interlink Daemon', style='bold red')
    console.log('Closing Websockify tunnels')
    console.print('Clean up successful', style='underline green')
    for _, process in ctrl_plane.ws_processes.items():
        console.log('Shutting down process', process.pid)
        process.kill()
    sys.exit(0)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    entry()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
