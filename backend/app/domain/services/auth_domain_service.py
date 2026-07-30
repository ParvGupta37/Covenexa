"""
Auth Domain Service.
Contains purely logical authentication rules (e.g. password complexity)
without I/O or repository calls.
"""
import re


class AuthDomainService:
    """
    Pure domain rules regarding authentication.
    Does not perform database calls or hash passwords (that's infrastructure).
    """

    @staticmethod
    def is_strong_password(password: str) -> bool:
        """
        Validates password strength.
        Rules:
          - At least 8 characters long
          - Contains at least one digit
          - Contains at least one uppercase letter
          - Contains at least one lowercase letter
          - Contains at least one special character
        """
        if len(password) < 8:
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[ !@#$%^&*()_+=\-\[\]{}|;:',.<>?/`~]", password):
            return False
        return True
