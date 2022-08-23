import glob
import os
import shutil
from contextlib import contextmanager
from io import BufferedReader, TextIOBase
from typing import Any, Dict, List

from dynaconf import Dynaconf, loaders
from dynaconf.utils.boxing import DynaBox
from dynaconf.vendor.box.exceptions import BoxKeyError
from securesystemslib.keys import decrypt_key, encrypt_key

from kaprien_api.tuf import Roles, StorageError
from kaprien_api.tuf.interfaces import IKeyVault, IStorage, ServiceSettings


class LocalStorage(IStorage):
    def __init__(self, path: str) -> None:
        self._path: str = path

    @classmethod
    def configure(cls, settings) -> None:
        os.makedirs(settings.LOCAL_STORAGE_BACKEND_PATH, exist_ok=True)

    @classmethod
    def settings(cls) -> List[ServiceSettings]:
        return [
            ServiceSettings(
                name="LOCAL_STORAGE_BACKEND_PATH",
                argument="path",
                required=True,
            ),
        ]

    @contextmanager
    def get(self, role, version=None) -> BufferedReader:
        """
        Yields TUF role metadata file object for the passed role name, from the
        configured TUF repo path, optionally at the passed version (latest if
        None).
        """

        if role == Roles.TIMESTAMP.value:
            filename = os.path.join(self._path, f"{role}.json")
        else:
            if version is None:
                filenames = glob.glob(
                    os.path.join(self._path, f"*.{role}.json")
                )
                versions = [
                    int(name.split("/")[-1].split(".", 1)[0])
                    for name in filenames
                ]
                try:
                    version = max(versions)
                except ValueError:
                    version = 1

            filename = os.path.join(self._path, f"{version}.{role}.json")

        file_object = None
        try:
            file_object = open(filename, "rb")
            yield file_object
        except OSError:
            raise StorageError(f"Can't open {filename}")
        finally:
            if file_object is not None:
                file_object.close()

    def put(self, file_object: TextIOBase, filename: str) -> None:
        """
        Writes passed file object to configured TUF repo path using the passed
        filename.
        """
        file_path = os.path.join(self._path, filename)
        if not file_object.closed:
            file_object.seek(0)

        try:
            with open(file_path, "wb") as destination_file:
                shutil.copyfileobj(file_object, destination_file)
                destination_file.flush()
                os.fsync(destination_file.fileno())
        except OSError:
            raise StorageError(f"Can't write file {filename}")


class LocalKeyVault(IKeyVault):
    def __init__(self, path: str):
        self._path: str = path
        self._secrets_file: str = os.path.join(self._path, ".secrets.yaml")
        self.keyvault = Dynaconf(
            envvar_prefix="LOCALKEYVAULT",
            settings_files=[self._secrets_file],
            environments=True,
        )

    @classmethod
    def configure(cls, settings):
        os.makedirs(settings.LOCAL_KEYVAULT_PATH, exist_ok=True)

    @classmethod
    def settings(cls):
        return [
            ServiceSettings(
                name="LOCAL_KEYVAULT_PATH",
                argument="path",
                required=True,
            ),
        ]

    def get(self, rolename: str):
        try:
            keys: Dict[str, Any] = self.keyvault.store[rolename]
        except BoxKeyError:
            raise ValueError(f"{rolename} not found.")
        keys_sslib_format: List[Dict[str, Any]] = []
        for key in keys:
            keys_sslib_format.append(decrypt_key(key["key"], key["password"]))

        return keys_sslib_format

    def put(self, rolename: str, keys: List[Dict[str, Any]]):
        key_vault_data: list = []
        for key in keys:
            ed25519_key = encrypt_key(key.get("key"), key.get("password"))
            key_vault_data.append(
                {
                    "key": ed25519_key,
                    "filename": key["filename"].split("/"),
                    "password": key["password"],
                }
            )

        self.keyvault.store[rolename.upper()] = key_vault_data
        data = self.keyvault.as_dict(env=self.keyvault.current_env)
        loaders.write(
            self._secrets_file,
            DynaBox(data).to_dict(),
            env=self.keyvault.current_env,
        )
