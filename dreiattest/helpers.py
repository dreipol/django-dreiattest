from typing import Optional, Union
from uuid import UUID


def is_valid_uuid(uuid: Optional[str] = None, version=4) -> bool:
    if not uuid:
        return False

    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid


