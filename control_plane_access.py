import requests


class ControlPlaneAccessInstance:
    token = ''
    host_secret = ''
    host_id = ''
    tenant_id = ''
    def __init__(self, base_url='http://100.81.35.39:3000'):
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
        return requests.post(f'{self.BASE_URL}/api/tenant/{self.tenant_id}/host/{self.host_id}/cmd', json={
            'secret': self.host_secret
        }).json()['data']
