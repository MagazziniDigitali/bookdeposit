import hashlib
from suds.client import Client


class User(object):

    def __init__(self, username, password):
        self.id = ""
        self.username = username
        self.password = password
        self.ip = "192.168.14.10"

        self.wsdl_base = "https://services.test.depositolegale.it/MagazziniDigitaliServices/services"
        self.wsdl_auth_software = (
            "{}/AuthenticationSoftwarePort?wsdl").format(self.wsdl_base)
        self.wsdl_auth_users = (
            "{}/AuthenticationUtentiPort?wsdl").format(self.wsdl_base)

        self.software_login = "BAGIT_MD"
        self.software_password = "Bagit_MD"

    def _sha256(self, string):
        return hashlib.sha256(string.encode('utf-8')).hexdigest()

    def _auth_software(self):
        client = Client(self.wsdl_auth_software, timeout=5)
        software_result = client.service.AuthenticationSoftwareOperation(
            self.software_login, self._sha256(self.software_password))
        return software_result

    def login(self):
        auth = {"login": self.username,
                "password": self._sha256(self.password)}

        client = Client(self.wsdl_auth_users, timeout=5)
        user_result = client.service.AuthenticationUtentiOperation(
            auth, self.ip, self._auth_software())

        if hasattr(user_result, "errorMsg"):
            error = user_result.errorMsg[0].errorType
            return {"status": "KO", "error": error}
        else:
            self.id = user_result.datiUtente.id
            return {"status": "OK", "user_id": user_result.datiUtente.id}
