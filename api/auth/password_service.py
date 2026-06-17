"""
PasswordService — encapsulates bcrypt hashing logic.

Pattern: Service Object (stateless, single responsibility).
"""
from __future__ import annotations

import bcrypt


class PasswordService:
    """
    Handles password hashing and verification using bcrypt.
    bcrypt 4.0+ enforces a 72-byte limit — handled internally.
    """

    _MAX_BYTES = 72

    def hash(self, password: str) -> str:
        """Returns a bcrypt hash of the password."""
        pwd_bytes = self._truncate(password)
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    def verify(self, plain: str, hashed: str) -> bool:
        """Returns True if plain matches the stored bcrypt hash."""
        pwd_bytes = self._truncate(plain)
        try:
            return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
        except ValueError:
            return False

    def _truncate(self, password: str) -> bytes:
        pwd_bytes = password.encode("utf-8")
        return pwd_bytes[:self._MAX_BYTES] if len(pwd_bytes) > self._MAX_BYTES else pwd_bytes
