from typing import Iterable, List
from backend.schemas import SinceResponse


def row_to_message(row) -> SinceResponse:
    return SinceResponse(
        user_id=row[0],
        role=row[1],
        content=row[2],
        created_at=row[3],
    )


def rows_to_messages(rows: Iterable) -> List[SinceResponse]:
    return [row_to_message(row) for row in rows]
