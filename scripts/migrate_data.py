"""
Script para migrar datos de SQLite a PostgreSQL.
Uso: python scripts/migrate_data.py
Requiere: PostgreSQL corriendo con DATABASE_URL o defaults locales.
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'peluqueria.db')
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://peluqueria:peluqueria@localhost:5432/peluqueria'
)

TABLES = [
    ('"user"', ['id', 'username', 'password_hash']),
    ('cliente', ['id', 'nombre', 'telefono', 'email', 'notas', 'fecha_registro']),
    ('cita', ['id', 'cliente_id', 'fecha', 'hora', 'servicio', 'precio', 'estado', 'notas', 'created_at']),
    ('pago', ['id', 'cliente_id', 'monto', 'concepto', 'metodo_pago', 'fecha']),
    ('producto', ['id', 'nombre', 'descripcion', 'precio', 'stock', 'categoria']),
    ('gasto', ['id', 'descripcion', 'monto', 'categoria', 'fecha']),
]


def migrate():
    conn_sqlite = sqlite3.connect(SQLITE_PATH)
    conn_sqlite.row_factory = sqlite3.Row

    conn_pg = psycopg2.connect(DATABASE_URL)
    cur = conn_pg.cursor()

    for table_pg, columns in TABLES:
        table_sqlite = 'user' if table_pg == '"user"' else table_pg
        rows = conn_sqlite.execute(f'SELECT * FROM {table_sqlite}').fetchall()
        if not rows:
            print(f'{table_pg}: 0 registros (sin datos)')
            continue

        columns_str = ', '.join(columns)
        values = []
        for row in rows:
            values.append(tuple(row[col] for col in columns))

        execute_values(
            cur,
            f'INSERT INTO {table_pg} ({columns_str}) VALUES %s',
            values
        )

        # Actualizar secuencia para IDs auto-increment
        seq_name = f'{table_sqlite}_id_seq'
        cur.execute(f"SELECT setval('{seq_name}', (SELECT MAX(id) FROM {table_pg}))")
        print(f'{table_pg}: {len(rows)} registros migrados')

    conn_pg.commit()
    cur.close()
    conn_pg.close()
    conn_sqlite.close()
    print('Migración completada exitosamente.')


if __name__ == '__main__':
    migrate()
