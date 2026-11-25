from django.db import connection


def verificar_banco() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
