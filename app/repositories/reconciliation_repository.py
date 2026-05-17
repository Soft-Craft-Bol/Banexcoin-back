from math import ceil

from sqlalchemy.orm import Session
from app.models.reconciliation import Reconciliation


def delete_reconciliations_by_upload(db: Session, upload_id: int):
    db.query(Reconciliation).filter(
        Reconciliation.upload_id == upload_id
    ).delete()
    db.commit()


def bulk_create_reconciliations(db: Session, items: list[dict]):
    if not items:
        return []

    records = [Reconciliation(**item) for item in items]

    db.add_all(records)
    db.commit()

    return records


def get_reconciliations(
    db: Session,
    upload_id: int | None = None,
    status: str | None = None,
    page: int = 0,
    size: int = 20,
):
    query = db.query(Reconciliation)

    if upload_id is not None:
        query = query.filter(Reconciliation.upload_id == upload_id)

    if status:
        query = query.filter(Reconciliation.status == status)

    total_elements = query.order_by(None).count()
    total_pages = ceil(total_elements / size) if total_elements else 0
    offset = page * size

    records = (
        query
        .order_by(Reconciliation.created_at.desc(), Reconciliation.id.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    number_of_elements = len(records)

    return {
        "content": records,
        "pageable": {
            "pageNumber": page,
            "pageSize": size,
            "offset": offset,
            "paged": True,
            "unpaged": False,
        },
        "totalElements": total_elements,
        "totalPages": total_pages,
        "last": page >= total_pages - 1 if total_pages > 0 else True,
        "first": page == 0,
        "size": size,
        "number": page,
        "numberOfElements": number_of_elements,
        "empty": number_of_elements == 0,
        "sort": {
            "sorted": True,
            "unsorted": False,
            "empty": False,
        },
    }