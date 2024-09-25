from functools import cached_property
from typing import Any, Optional

class TradingHoursError(Exception):
    """Baseclass for all errors from this library"""

    def __init__(self, message: str, inner: Optional[Exception] = None):
        super().__init__(message, inner)
        self._message = message
        self._inner = inner

    @property
    def message(self):
        return self._message

    @property
    def inner(self):
        return self._inner

    @cached_property
    def detail(self):
        return self.build_detail()

    @cached_property
    def help_message(self):
        return self.build_help_message()

    def build_detail(self, message: Optional[str] = None):
        message = message or self.message
        if self.inner:
            message = f"{message} ({self.inner})"
        return message

    def build_help_message(self):
        return None

    def __str__(self):
        return self.detail


class PrepareError(TradingHoursError):
    """Happens when a field from a model cannot be interpreted"""

    def __init__(self, field: "Field", value: Any, inner: Optional[Exception] = None):
        super().__init__("Error preparing field", inner=inner)
        self._field = field
        self._value = value

    @property
    def field(self):
        return self._field

    @property
    def value(self):
        return self._value

    def build_detail(self):
        message = f"Could not prepare field {self._field.field_name}"
        return super().build_detail(message)


class ClientError(TradingHoursError):
    """When an error occurs accessing remote HTTP server"""

    pass


class TokenError(ClientError):
    """When server access fails because of an invalid token"""

    def build_help_message(self):
        return (
            "A TradingHours token is required to perform this operation. "
            "You can access https://www.tradinghours.com/user/api-tokens to "
            "obtain one. In case you already have a token, remember to make "
            "it available by exporting the environment variable "
            "TRADINGHOURS_TOKEN and try again."
        )


class MissingDefinitionError(TradingHoursError):
    """When a season definition is not found"""

    pass


class MissingSqlAlchemyError(TradingHoursError):
    """When SQL Alchemy is not installed"""

    def build_help_message(self):
        return (
            "You need to install SQLAlchemy in order to use database "
            "ready store. You should be able to do that by running "
            "`pip install tradinghours[sql]` from the command line."
        )

class NoAccess(TradingHoursError):
    """
    Raised when a user attempts accessing a type of data
    that is not available under their current plan.
    """
    pass

class NotCovered(TradingHoursError):
    """
    Raised when a user attempts to access a specific data item
     that is not covered by Tradinghours but the type of data
     (e.g.: Currencies) are available under their current plan.
    """
    pass

class MICDoesNotExist(TradingHoursError):
    """
    Raised when a user tries to get a Market with a mic that can not
     be matched with a finid.
    """
    pass

class MissingTzdata(TradingHoursError):
    pass

class DBError(TradingHoursError):
    """
    Raise when the database could not be accessed
    """
    pass

