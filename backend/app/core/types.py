"""
Portable column types shared across ORM models.

MySQL has no native UUID column type, so GUID stores UUIDs as CHAR(36)
and transparently converts to/from uuid.UUID at the Python boundary.
Model code therefore keeps working with real UUID objects.
"""

import uuid
from typing import Optional

from sqlalchemy import CHAR
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator):
    """
    Platform-independent UUID column, stored as CHAR(36) in MySQL.

    Binds accept either a uuid.UUID or a string; results are always
    returned as uuid.UUID so callers never deal with the storage format.
    """

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect) -> Optional[uuid.UUID]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
