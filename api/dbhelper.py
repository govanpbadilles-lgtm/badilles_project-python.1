import os
import sqlite3
from sqlite3 import Row
from db.dbhelper import *


# --- Path to your SQLite database file ---
database = os.path.join("db", "school.db")


# --- Helper for SELECT queries ---
def getprocess(sql: str, vals: list = []) -> list:
    try:
        conn = sqlite3.connect(database)
        conn.row_factory = Row
        cursor = conn.cursor()
        cursor.execute(sql, vals)
        data = cursor.fetchall()
    except Exception as e:
        print(f"[DB ERROR] {e}")
        data = []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    # Convert rows to list of dictionaries
    return [dict(row) for row in data]


# --- Helper for INSERT / UPDATE / DELETE ---
def postprocess(sql: str, vals: list = []) -> bool:
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute(sql, vals)
        conn.commit()
        result = cursor.rowcount > 0
    except Exception as e:
        print(f"[DB ERROR] {e}")
        result = False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    return result


# --- Get all records (with optional search) ---
def getall(table: str, search: str = None) -> list:
    sql = f"SELECT * FROM {table}"
    vals = []

    if search:
        search_term = f"%{search}%"
        where_clause = (
            " WHERE idno LIKE ? OR lastname LIKE ? OR firstname LIKE ? OR course LIKE ?"
        )
        sql += where_clause
        vals = [search_term] * 4
        print(f"[DB DEBUG] Search SQL: {sql} -> {vals}")

    sql += " ORDER BY idno ASC"
    return getprocess(sql, vals)


# --- Get specific record(s) ---
def getrecord(table: str, **kwargs) -> list:
    if not kwargs:
        return []
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    where_clause = " AND ".join([f"{key}=?" for key in keys])
    sql = f"SELECT * FROM {table} WHERE {where_clause}"
    print(f"[DB DEBUG] {sql} -> {vals}")
    return getprocess(sql, vals)


# --- Add new record ---
def addrecord(table: str, **kwargs) -> bool:
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    placeholders = ",".join(["?"] * len(keys))
    fields = ",".join(keys)
    sql = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
    print(f"[DB DEBUG] {sql} -> {vals}")
    return postprocess(sql, vals)


# --- Delete record ---
def deleterecord(table: str, **kwargs) -> bool:
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    where_clause = " AND ".join([f"{key}=?" for key in keys])
    sql = f"DELETE FROM {table} WHERE {where_clause}"
    print(f"[DB DEBUG] {sql} -> {vals}")
    return postprocess(sql, vals)


# --- Update record by idno ---
def updaterecord(table: str, idno: int, **kwargs) -> bool:
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    set_clause = ", ".join([f"{key}=?" for key in keys])
    sql = f"UPDATE {table} SET {set_clause} WHERE idno=?"
    vals.append(idno)
    print(f"[DB DEBUG] {sql} -> {vals}")
    return postprocess(sql, vals)

