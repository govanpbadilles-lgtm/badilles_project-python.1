
import os
import sys
from flask import Flask, render_template, redirect, url_for, request, jsonify
from werkzeug.utils import secure_filename

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
