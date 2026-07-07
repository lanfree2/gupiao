"""定时抓取到期节点。用法: python -m app.worker.run"""
from app.database import SessionLocal
from app.services.tracking import process_due_nodes


def main():
    db = SessionLocal()
    try:
        result = process_due_nodes(db)
        print("Worker done:", result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
