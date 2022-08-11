# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from abc import ABC
from dataclasses import dataclass
from io import TextIOBase
from typing import Any, Dict, List

from tuf.api import exceptions  # noqa
from tuf.api.metadata import (  # type: ignore noqa
    Metadata,
    StorageBackendInterface,
    T,
)


@dataclass
class ServiceSettings:
    name: str
    argument: str
    required: bool


class IKeyVault(ABC):
    @classmethod
    def configure(cls, settings):
        """
        Run actions to test, configure using the settings
        """
        raise NotImplementedError

    @classmethod
    def settings(cls):
        """
        Define all the ServiceSettings required in settings
        """
        raise NotImplementedError

    def get(self, rolename: List[str]) -> Dict[str, Any]:
        """Return a key from specific rolename"""
        raise NotImplementedError

    def put(self, file_object: str, filename: str) -> None:
        """
        Stores file object with a specific filename.
        """
        raise NotImplementedError


class IStorage(StorageBackendInterface):
    @classmethod
    def configure(cls, settings: Any):
        """
        Run actions to test, configure using the settings
        """
        raise NotImplementedError

    @classmethod
    def settings(cls) -> List[ServiceSettings]:
        """
        Define all the ServiceSettings required in settings
        """
        raise NotImplementedError

    def get(self, rolename: str, version: int) -> "Metadata[T]":
        """
        Return metadata from specific role name, optionally specific version.
        """
        raise NotImplementedError

    def put(self, file_object: TextIOBase, filename: str) -> None:
        """
        Stores file object with a specific filename.
        """
        raise NotImplementedError
