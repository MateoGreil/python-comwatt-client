from __future__ import annotations

import hashlib

from ._core import _BaseClient, _api_error


class AuthMixin(_BaseClient):
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(f'jbjaonfusor_{password}_4acuttbuik9'.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> None:
        """
        Authenticates a user with the provided username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            None

        Raises:
            Exception: If the authentication fails.

        """

        password_hash = self._hash_password(password)
        self._post_authent(username, password_hash)

        self._username = username
        self._auth_hash = password_hash

    def is_authenticated(self) -> bool:
        """
        Checks whether the current session cookie is still accepted by the API.

        Args:
            None

        Returns:
            bool: True if the session is authenticated, False if the API
                rejected it (401/403).

        Raises:
            Exception: If an unexpected error occurs while probing the API.

        """

        url = f'{self.base_url}/users/authenticated'

        response = self.session.get(url, timeout=self.timeout)
        if response.status_code == 200:
            return True
        elif response.status_code in (401, 403):
            return False
        else:
            raise _api_error(response)
