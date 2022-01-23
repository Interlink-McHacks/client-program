import requests


class ControlPlaneAccessInstance:
    token = ''
    host_secret = ''
    host_id = ''
    tenant_id = ''
    tunnels = []
    ws_processes = {}

    def __init__(self, base_url='http://api.interlink.rest'):
        self.BASE_URL = base_url

    def login(self, email, password):
        """
        Returns auth token if request valid

        :param email: user email
        :param password: user password
        :return: base64 encoded JWT token
        """
        r = requests.post(f'{self.BASE_URL}/api/login', json={
            'email': email,
            'password': password
        })
        self.token = r.json()['data']['token']
        return self.token

    def enroll(self, tenant_id, join_token, name, contact_point):
        return requests.post(f'{self.BASE_URL}/api/tenant/{tenant_id}/host', json={
            'joinToken': join_token,
            'name': name,
            'contactPoint': contact_point
        }).json()

    def contact_cmd(self):
        r = requests.post(f'{self.BASE_URL}/api/tenant/{self.tenant_id}/host/{self.host_id}/cmd', json={
            'secret': self.host_secret
        }).json()
        return r['data']

    def diff_cmd_result_and_update(self, new_tunnel):
        result = {
            'add': [],
            'remove': []
        }

        new_tun_ids = {i['_id'] for i in new_tunnel}
        old_tun_ids = {i['_id'] for i in self.tunnels}

        add_tun_ids = new_tun_ids.difference(old_tun_ids)
        del_tun_ids = old_tun_ids.difference(new_tun_ids)

        tuns = {i['_id']: i for i in self.tunnels + new_tunnel}

        for idx in add_tun_ids:
            result['add'].append(tuns[idx])
        for idx in del_tun_ids:
            result['remove'].append(tuns[idx])

        self.tunnels = [tuns[i] for i in new_tun_ids.intersection(old_tun_ids).union(add_tun_ids)]
        return result
