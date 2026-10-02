import json

from backend.app.db.database import get_connection


class FaceRepository:

    def save(self, person_id, embedding):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            query = """
                INSERT INTO rostros (
                    person_id,
                    embedding,
                    activo
                )
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE
                    embedding = VALUES(embedding),
                    activo = TRUE,
                    fecha_registro = CURRENT_TIMESTAMP
            """

            cursor.execute(
                query,
                (
                    str(person_id),
                    json.dumps(embedding.tolist())
                )
            )

            connection.commit()

        finally:
            cursor.close()
            connection.close()

    def find_by_person_id(self, person_id):
        connection = get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    person_id,
                    embedding
                FROM rostros
                WHERE person_id = %s
                  AND activo = TRUE
                LIMIT 1
            """

            cursor.execute(
                query,
                (str(person_id),)
            )

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

    def find_all(self):
        connection = get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    person_id,
                    embedding
                FROM rostros
                WHERE activo = TRUE
            """

            cursor.execute(query)

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()

    def deactivate(self, person_id):
        connection = get_connection()

        try:
            cursor = connection.cursor()

            query = """
                UPDATE rostros
                SET activo = FALSE
                WHERE person_id = %s
            """

            cursor.execute(
                query,
                (str(person_id),)
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:
            cursor.close()
            connection.close()


face_repository = FaceRepository()