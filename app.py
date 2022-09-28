import os.path
import eyed3
from flask import Flask, render_template, request, redirect, flash, Response
from secrets import token_hex
from models import Artist, Album, Track
from hashlib import md5
from datetime import timedelta


app = Flask(__name__)
app.secret_key = token_hex()
app.config['ALLOWED_EXTENSIONS'] = ['.mp3']
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER, exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    context = []
    for r in Track.select():
        context.append([r.file_name, r.title, r.artist.name, r.album.title, timedelta(seconds=r.duration), r.id])
    return render_template('index.html', files=context)


@app.route('/', methods=['POST'])
def upload_files():
    delete_id = request.form.get('delete')
    if delete_id:
        query = Track.get(Track.id == delete_id)
        os.remove(os.path.join(UPLOAD_FOLDER, query.file_name))
        query.delete_instance()
        flash('File successfully deleted')
        return redirect('/')
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    filename = file.filename
    if filename == '':
        flash('No file selected for uploading')
        return redirect(request.url)
    else:
        root, file_ext = os.path.splitext(filename)
        if file_ext in app.config['ALLOWED_EXTENSIONS']:
            temp_path = os.path.join(TEMP_FOLDER, filename)
            file.save(os.path.join(TEMP_FOLDER, filename))
            eyed3_file = eyed3.load(temp_path)
            if eyed3_file.tag.artist is None or eyed3_file.tag.title is None:
                flash('Wrong meta information')
                os.remove(temp_path)
                return redirect(request.url)
            file_md5 = md5(f'{eyed3_file.tag.title}{eyed3_file.tag.artist}{eyed3_file.info.time_secs}'
                           .encode()).hexdigest()
            query = Track.select().where(Track.md5 == file_md5)
            if query.exists():
                flash('File already exist')
                os.remove(temp_path)
                return redirect(request.url)

            query = Artist.select().where(Artist.name == eyed3_file.tag.artist)
            if query.exists():
                artist = query[0].id
            else:
                artist = Artist(name=eyed3_file.tag.artist).save()

            query = Album.select().where(Album.title == eyed3_file.tag.album)
            if query.exists():
                album = query[0].id
            else:
                album = Album(
                    title=eyed3_file.tag.album,
                    recording_date=eyed3_file.tag.recording_date.year if eyed3_file.tag.recording_date else None,
                    artist=artist
                ).save()

            Track(
                title=eyed3_file.tag.title,
                duration=eyed3_file.info.time_secs,
                album=album,
                artist=artist,
                file_name=filename,
                md5=file_md5
            ).save()

            os.rename(temp_path, os.path.join(UPLOAD_FOLDER, filename))
            flash('File uploaded successfully')
            return redirect('/')
        else:
            flash('Not allowed file type')
            return redirect(request.url)


@app.route("/<path:filename>")
def stream(filename):
    def generate():
        path = os.path.join(UPLOAD_FOLDER, filename)
        with open(path, "rb") as f:
            data = f.read(1024)
            while data:
                yield data
                data = f.read(1024)
    return Response(generate(), mimetype="audio/x-wav")


if __name__ == '__main__':
    app.run(debug=False)
