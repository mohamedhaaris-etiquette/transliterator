from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


class EncryptedTextField(models.TextField):
    """
    TextField that stores values as Fernet ciphertext in the database and
    returns plaintext to application code when values are read through Django.
    """

    encryption_prefix = "fernet$"

    def _get_fernet(self):
        key = getattr(settings, "TRANSCRIPT_ENCRYPTION_KEY", "")

        if not key:
            raise ImproperlyConfigured(
                "TRANSCRIPT_ENCRYPTION_KEY is missing. "
                "Add a Fernet key to the loaded .env file."
            )

        if isinstance(key, str):
            key = key.encode("utf-8")

        try:
            return Fernet(key)
        except (TypeError, ValueError) as exc:
            raise ImproperlyConfigured(
                "TRANSCRIPT_ENCRYPTION_KEY is not a valid Fernet key."
            ) from exc

    def _decrypt_value(self, value):
        token = value[len(self.encryption_prefix) :]

        try:
            return (
                self._get_fernet()
                .decrypt(token.encode("utf-8"))
                .decode("utf-8")
            )
        except (InvalidToken, UnicodeDecodeError) as exc:
            raise ValueError(
                "Transcript text could not be decrypted. "
                "The encryption key is incorrect or the stored value is corrupted."
            ) from exc

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        value = super().to_python(value)

        if value in (None, ""):
            return value

        if value.startswith(self.encryption_prefix):
            return self._decrypt_value(value)

        # Supports existing plaintext rows until the data migration encrypts them.
        return value

    def get_prep_value(self, value):
        # Call the base Field implementation directly so encrypted values are not
        # passed through this class's decrypting to_python() method first.
        value = models.Field.get_prep_value(self, value)

        if value is None:
            return None

        value = str(value)

        if value == "":
            return ""

        # Avoid double-encryption if raw ciphertext is explicitly supplied.
        if value.startswith(self.encryption_prefix):
            try:
                self._decrypt_value(value)
                return value
            except ValueError:
                # A legitimate plaintext value may start with the prefix.
                pass

        token = (
            self._get_fernet()
            .encrypt(value.encode("utf-8"))
            .decode("utf-8")
        )
        return f"{self.encryption_prefix}{token}"







