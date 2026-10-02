from datetime import date, datetime, time

from backend.app.db.attendance_repository import attendance_repository


def main():
    attendance_id = attendance_repository.save(
        person_id="TEST_REPO",
        attendance_date=date.today(),
        attendance_time=datetime.now().time().replace(microsecond=0),
        confidence=0.95,
        liveness_score=12.50,
        status="PRESENTE"
    )

    print("ID GUARDADO:", attendance_id)

    exists = attendance_repository.exists_today(
        "TEST_REPO"
    )

    print("EXISTE HOY:", exists)

    records = attendance_repository.find_all()

    print("ASISTENCIAS EN BD:")

    for record in records:
        print(record)

    if not exists:
        raise RuntimeError(
            "La asistencia no fue encontrada"
        )

    print("ATTENDANCE REPOSITORY PERSISTENCE OK")


if __name__ == "__main__":
    main()