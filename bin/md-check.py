#!/usr/bin/env python

import hashlib
import sys
import subprocess
import os
import time
from suds.client import Client


class MDCheck(object):

    def __init__(self, filename, digest, mtime):
        self.id = ""
        self.filename = filename
        self.digest = digest
        self.mtime = mtime
        self.ip = "192.168.14.10"

        self.wsdl_base = "http://md-services.test.bncf.lan/MagazziniDigitaliServices/services"

        self.wsdl_auth_software = (
            "{}/AuthenticationSoftwarePort?wsdl").format(self.wsdl_base)

        self.wsdl_check_md = (
            "{}/CheckMDPort?wsdl").format(self.wsdl_base)

        self.software_login = "BAGIT_MD"
        self.software_password = "Bagit_MD"

    def _sha256(self, string):
        return hashlib.sha256(string.encode('utf-8')).hexdigest()

    def _auth_software(self):
        client = Client(self.wsdl_auth_software, timeout=5)
        software_result = client.service.AuthenticationSoftwareOperation(
            self.software_login, self._sha256(self.software_password))
        return software_result

    def status(self):
        args = {"nomeFile": self.filename,
                "digest": {"digestType": "SHA1", "digestValue": self.digest},
                "ultimaModifica": self.mtime}

        client = Client(self.wsdl_check_md, timeout=5)
        check_result = client.service.CheckMDOperation(
            self._auth_software(), args)

        return check_result.oggettoDigitale.statoOggettoDigitale


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <file>' % sys.argv[0])

    file_to_check = sys.argv[1]

    sha1_out = subprocess.check_output(
        "/usr/local/bin/gsha1sum {}|cut -d' ' -f1".format(file_to_check), shell=True)
    sha1 = sha1_out.decode("utf-8").strip()
    mtime = time.strftime("%Y-%m-%dT%H:%M:%S",
                          time.gmtime(os.path.getmtime(file_to_check)))

    check = MDCheck(file_to_check, sha1, mtime)
    print(check.status())

if __name__ == '__main__':
    main()
