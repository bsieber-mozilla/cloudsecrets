import base64
import json
import logging
import os

class SecretsBase:
    def __init__(self,secret,**kwargs) -> None:
        logging.getLogger(__name__)
        self._secrets = {}
        self._encoded_secrets = {}
        self.secret = secret
        self._version = kwargs.get("version","1")
    @property
    def secrets(self) -> dict:
        return self._secrets
    @property
    def version(self) -> str:
        return self._version
    @property
    def project(self) -> str:
        return self._project
    @property
    def _secret_exists(self) -> bool:
        return True
    def __iter__(self) -> iter:
        return iter(self._secrets.items())
    def _load_secrets(self) -> None:
        self._version = "1"
    def _create_secret_resource(self) -> None:
        pass
    def update(self) -> None:
        pass
    def set(self,key,val) -> None:
        """
        The key/val here aren't the key/val of secretmanager, they're a key/val within a given secret val.
        """
        if type(val) != str:
            logging.warn("Warning, value is not a string so serializing as json")
            val = json.dumps(val)
        if key in self._secrets:
            logging.warn("Warning, you are overwriting an existing key")
        self._secrets[key] = val
        self._encoded_secrets[key] = base64.b64encode(bytes(val,'utf-8')).decode('ascii')
        self.update()

    def unset(self,key) -> None:
        """
        Unset (delete) a secret key
        """
        if key in self._secrets:
            del self._secrets[key]
        if key in self._encoded_secrets:
            del self._encoded_secrets[key]
        self.update()

    def rollback(self,version=-1) -> None:
        if version < 0:
            version = int(self._version) + int(version)
        self._load_secrets()

class EnvSecrets(SecretsBase):
    def __init__(self,secret=None,**kwargs) -> None:
        super().__init__(secret,**kwargs)
        self._load_secrets()
    def _load_secrets(self) -> None:
        for k,v in os.environ.items():
            self.set(k,v)
    def update(self) -> None:
        self._version = str(int(self._version) + 1)

class FileSecrets(SecretsBase):
    def __init__(self,filename,**kwargs) -> None:
        super().__init__("",**kwargs)
        self.filename = filename
        self.create_if_not_present = kwargs.get('create_if_not_present',True)
        self._load_secrets()
    def _load_secrets(self) -> None:
        if not os.path.exists(self.filename) and self.create_if_not_present:
            f = open(self.filename,'w')
            f.write('{}')
            f.close()
        j_blob = open(self.filename).read()
        d = json.loads(j_blob)
        for k,v in d.items():
            self.set(k,v)
    def update(self) -> None:
        """
        write secret state back to the file
        """
        j_blob = json.dumps(self._encoded_secrets)
        f = open(self.filename,'w')
        f.write(j_blob)
        f.close()
        self._version = str(int(self._version) + 1)

