from sqlalchemy.orm import Session

from app.models.reported_balance import ReportedBalance


def bulk_create_reported_balances(db: Session, items: list[dict]):
    if not items:
        return []

    records = [ReportedBalance(**item) for item in items]

    db.add_all(records)
    db.commit()

    return records


def delete_reported_balances_by_upload(db: Session, upload_id: int):
    db.query(ReportedBalance).filter(
        ReportedBalance.upload_id == upload_id
    ).delete()
    db.commit()


def get_reported_balances(db: Session, upload_id: int):
    return (
        db.query(ReportedBalance)
        .filter(ReportedBalance.upload_id == upload_id)
        .order_by(ReportedBalance.client, ReportedBalance.period)
        .all()
    )