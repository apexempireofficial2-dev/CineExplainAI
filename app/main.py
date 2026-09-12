from flask import Flask, render_template, request, jsonify
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

from app.services.ai_script import improve_movie_script

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {
    "mp4", "mkv", "mov", "avi", "webm", "m4v"
}

ALLOWED_SCRIPT_EXTENSIONS = {
    "txt"
}

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 * 1024


def allowed_video(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_VIDEO_EXTENSIONS
    )


def allowed_script(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_SCRIPT_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/upload-video", methods=["POST"])
def upload_video():

    if "video" not in request.files:
        return jsonify({
            "success": False,
            "error": "No video selected"
        }), 400

    video = request.files["video"]

    if not video.filename:
        return jsonify({
            "success": False,
            "error": "No filename"
        }), 400

    if not allowed_video(video.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported video format"
        }), 400

    file_id = uuid.uuid4().hex

    extension = video.filename.rsplit(".", 1)[1].lower()

    filename = f"{file_id}.{extension}"

    destination = UPLOAD_DIR / secure_filename(filename)

    video.save(destination)

    return jsonify({
        "success": True,
        "job_id": file_id,
        "filename": filename,
        "message": "Video uploaded successfully"
    })


@app.route("/api/upload-script", methods=["POST"])
def upload_script():

    if "script" not in request.files:
        return jsonify({
            "success": False,
            "error": "No script selected"
        }), 400

    script = request.files["script"]

    if not script.filename:
        return jsonify({
            "success": False,
            "error": "No filename"
        }), 400

    if not allowed_script(script.filename):
        return jsonify({
            "success": False,
            "error": "Only .txt script files are supported"
        }), 400

    file_id = uuid.uuid4().hex

    filename = f"{file_id}.txt"

    destination = UPLOAD_DIR / filename

    script.save(destination)

    return jsonify({
        "success": True,
        "script_id": file_id,
        "filename": filename,
        "path": str(destination),
        "message": "Script uploaded successfully"
    })


@app.route("/api/improve-script", methods=["POST"])
def improve_script():

    data = request.get_json(silent=True) or {}

    script_id = data.get("script_id")

    language = data.get("language", "Hindi")
    style = data.get("style", "Cinematic")

    if not script_id:
        return jsonify({
            "success": False,
            "error": "script_id missing"
        }), 400

    script_path = UPLOAD_DIR / f"{script_id}.txt"

    if not script_path.exists():
        return jsonify({
            "success": False,
            "error": "Uploaded script not found"
        }), 404

    output_path = OUTPUT_DIR / f"{script_id}_improved.txt"

    try:

        improve_movie_script(
            script_path,
            output_path,
            language=language,
            style=style
        )

        improved_text = output_path.read_text(
            encoding="utf-8"
        )

        return jsonify({
            "success": True,
            "script_id": script_id,
            "output": str(output_path),
            "text": improved_text
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(413)
def file_too_large(error):

    return jsonify({
        "success": False,
        "error": "File is too large. Maximum size is 10 GB."
    }), 413


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
