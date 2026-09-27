from datetime import date

from backend.app.db.database import get_connection


class AttendanceRepository:

    def save(
        self,
        person_id,
        attendance_date,
        attendance_time,
        confidence,
        liveness_score,
        status
    ):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            query = """
                INSERT INTO asistencias (
                    person_id,
                    fecha,
                    hora,
                    confianza,
                    liveness_score,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    str(person_id),
                    attendance_date,
                    attendance_time,
                    float(confidence),
                    float(liveness_score),
                    status
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:
            cursor.close()
            connection.close()

    def exists_today(self, person_id, current_date=None):
        if current_date is None:
            current_date = date.today()

        connection = get_connection()

        try:
            cursor = connection.cursor()

            query = """
                SELECT COUNT(*)
                FROM asistencias
                WHERE person_id = %s
                  AND fecha = %s
            """

            cursor.execute(
                query,
                (
                    str(person_id),
                    current_date
                )
            )

            count = cursor.fetchone()[0]

            return count > 0

        finally:
            cursor.close()
            connection.close()

    def find_all(self):
        connection = get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    id,
                    person_id,
                    fecha,
                    hora,
                    confianza,
                    liveness_score,
                    estado,
                    fecha_registro
                FROM asistencias
                ORDER BY fecha DESC, hora DESC
            """

            cursor.execute(query)

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()


attendance_repository = AttendanceRepository()