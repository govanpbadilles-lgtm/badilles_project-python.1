
import os
import sys
from flask import Flask, render_template, redirect, url_for, request, jsonify

import os
import sqlite3
from sqlite3 import Row

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


# --- Import DB Helper ---
sys.path.insert(0, "db/")
from dbhelper import *  # Must contain: getall(), getrecord(), addrecord(), updaterecord(), deleterecord()

# --- Flask Config ---
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
DEFAULT_IMAGE = os.path.join("static", "images", "account.jpg")


# --- Home Page ---
@app.route("/", methods=["GET"])
def index():
    students = getall("students") or []
    return render_template("index.html", studentlist=students)


# --- Add Student ---
@app.route("/add_student", methods=["POST"])
def add_student():
    idno = request.form.get("idno")
    lastname = request.form.get("lastname")
    firstname = request.form.get("firstname")
    course = request.form.get("course")
    level = request.form.get("level")

    if not all([idno, lastname, firstname, course, level]):
        return redirect(url_for("index"))

    profile = request.files.get("profile")
    profile_path = DEFAULT_IMAGE

    if profile and profile.filename != "":
        filename = secure_filename(f"{idno}_{profile.filename}")
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        profile.save(filepath)
        profile_path = filepath.replace("\\", "/")

    addrecord(
        "students",
        idno=idno,
        lastname=lastname,
        firstname=firstname,
        course=course,
        level=level,
        image=profile_path
    )
    return redirect(url_for("index"))


# --- Update Student ---
@app.route("/update_student/<int:idno>", methods=["POST"])
def update_student(idno):
    record = getrecord("students", idno=idno)
    if not record:
        return redirect(url_for("index"))

    old_profile = record[0].get("image", DEFAULT_IMAGE)
    profile = request.files.get("profile")
    new_profile = old_profile

    if profile and profile.filename != "":
        if old_profile != DEFAULT_IMAGE and os.path.exists(old_profile):
            os.remove(old_profile)
        filename = secure_filename(f"{idno}_{profile.filename}")
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        profile.save(filepath)
        new_profile = filepath.replace("\\", "/")

    updaterecord(
        "students",
        idno=idno,
        lastname=request.form.get("lastname"),
        firstname=request.form.get("firstname"),
        course=request.form.get("course"),
        level=request.form.get("level"),
        image=new_profile
    )
    return redirect(url_for("index"))


# --- Delete Student ---
@app.route("/delete/<idno>", methods=["POST"])
def delete_student(idno):
    record = getrecord("students", idno=idno)
    if record:
        profile_url = record[0].get("image", DEFAULT_IMAGE)
        if profile_url != DEFAULT_IMAGE and os.path.exists(profile_url):
            os.remove(profile_url)
    deleterecord("students", idno=idno)
    return jsonify({"message": f"Student {idno} deleted successfully!"})


# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
