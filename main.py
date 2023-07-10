#!/usr/bin/env python3

import pandas as pd
import os
from flask import (
    Flask,
    flash,
    render_template,
    request,
    redirect,
    g,
    url_for,
    send_from_directory,
    send_file,
    abort,
)
from werkzeug.utils import secure_filename
import numpy as np

__author__ = "Christopher J. Blakeney"
__version__ = "0.1.0"
__license__ = ""

# Flask app nonsense
app = Flask(__name__)
app.config["UPLOAD_PATH"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.config["UPLOAD_EXTENSIONS"] = [".xlsx"]
app.secret_key = "pickledonions"


@app.errorhandler(413)
def too_large(e):
    return "ERROR: File is too large", 413


def not_found():
    return render_template("error.html")


def create_routine(df, s, i, n):
    # CLEAN DATA
    # change all user input and df columns to lowercase and strip whitespace
    s = s.lower().strip()
    i = i.lower().strip()
    df["Split"] = df["Split"].str.lower().str.strip()
    df["Implement"] = df["Implement"].str.lower().str.strip()
    df = df.astype(str)

    # filter df for split and implement choice
    proto = df[
        df["Split"].str.contains(s, na=False)
        & (df["Implement"].str.contains(i, na=False))
    ]
    # convert sets column to int
    proto = proto.astype({"Sets": "int"})
    # take random (n) sample of proto
    proto = proto.sample(n, ignore_index=True)
    # start index at 1 instead of 0
    proto.index = proto.index + 1
    # remove unwanted columns
    proto["Reps x Sets"] = proto["Reps"].astype(str) + " x " + proto["Sets"].astype(str)
    proto = proto.drop(
        ["Reps", "Sets", "Split"],
        axis=1,
    )
    return proto


def validate_xlsx(xlsx):
    output = True
    df = pd.read_excel(xlsx)
    col_names = ["Implement", "Exercise", "Reps", "Sets", "Split"]
    # check column titles
    for col in df.columns:
        if col not in col_names:
            output = False
    # check null values
    if df.isnull().values.any():
        output = False
    return output


def validate_input(split, implement, xlsx):
    df = pd.read_excel(xlsx)
    s = df.Split.tolist()
    imp = df.Implement.tolist()
    if split not in s or implement not in imp:
        return False
    return True


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("upload-excel.html")


@app.route("/download")
def download_file():
    path = "static/template.xlsx"
    return send_file(path, as_attachment=True)


@app.route("/output", methods=["GET", "POST"])
def process_xlsx():
    split = request.form.get("split")
    implement = request.form.get("imp")
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename != "":
        if validate_input(split, implement, filename) is not True:
            error = "Invalid input, ensure split and implement choices exist in your database"
            return render_template("error.html", e=error)
        file_ext = os.path.splitext(filename)[1]
        if (
            file_ext not in app.config["UPLOAD_EXTENSIONS"]
            or validate_xlsx(filename) != True
        ):
            # what happens when file input is not .xlsx OR invalid spreaadsheet formatting
            error = "Invalid file, please ensure you are uploading a .xlsx file with correct formatting"
            return render_template("error.html", e=error)
        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filename))
    dataset = pd.read_excel(os.path.join(app.config["UPLOAD_PATH"], filename))
    # change n for more/less exercises
    df = create_routine(dataset, split, implement, n=6)
    tables = [df.to_html(classes="data")]
    titles = [" "]
    return render_template("output.html", tables=tables, titles=titles)


@app.route("/help", methods=["GET"])
def help():
    return render_template("help.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
