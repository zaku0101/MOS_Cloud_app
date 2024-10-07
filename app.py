from flask import Flask
from flask import *
from flask import render_template,send_file, abort
from pathlib import Path
import shutil, os, datetime, random
import datetime as dt
import ftplib
import io

app = Flask(__name__, static_folder="static", template_folder="template")

FTP_HOST = "localhost"

def get_ftp_connection():
    ftp = ftplib.FTP(FTP_HOST)
    ftp.login()
    return ftp

@app.route('/')
def main_page():
    return render_template("index.html")
@app.route('/login')
def logging_page():
        return render_template("login.html")

def get_readable_byte_size(num, suffix='B') -> str:
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def get_time_stamp_string(tsec: float) -> str:
    tobj = dt.datetime.fromtimestamp(tsec)
    tstr = dt.datetime.strftime(tobj, '%Y-%m-%d %H:%M')
    return tstr
def get_icon_class_for_filename(fname):
    file_ext = Path(fname).suffix
    file_ext = file_ext[1:] if file_ext.startswith(".") else file_ext
    file_types = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg", "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql", "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    file_icon_class = f"bi bi-filetype-{file_ext}" if file_ext in file_types else "bi bi-file-earmark"
    return file_icon_class


@app.route('/drive/' ,defaults={'req_path' : ''})
@app.route('/drive/<path:req_path>')
def get_files(req_path):    
    ftp = get_ftp_connection()
    try:
        ftp.cwd(req_path)
    except:
        return abort(404)
    file_objs = []
    try:
        for name in ftp.nlst():
            try:
                size = ftp.size(name)
                mtime = ftp.sendcmd(f"MDTM {name}")[4:].strip()
                mtime = dt.datetime.strptime(mtime, '%Y%m%d%H%M%S').timestamp()
                file_objs.append({
                    'name': name,
                    'fIcon': get_icon_class_for_filename(name),
                    'relPath': os.path.join(req_path, name).replace("\\", "/"),
                    'mTime': get_time_stamp_string(mtime),
                    'size': get_readable_byte_size(size)
                })
            except ftplib.error_perm:
                file_objs.append({
                    'name': name,
                    'fIcon': "bi bi-folder-fill",
                    'relPath': os.path.join(req_path, name).replace("\\", "/"),
                    'mTime': '',
                    'size': ''
                })
    finally:
        ftp.quit()

    parent_folder = os.path.dirname(req_path)
    return render_template('drive.html', data={'files': file_objs, 'parentFolder': parent_folder})
    
    
@app.route('/download/<path:filename>')
def download_file(filename):
    ftp = get_ftp_connection()
    try:
        try:
            ftp.cwd(filename)
            return get_files(filename)
        except ftplib.error_perm:
            bio = io.BytesIO()
            ftp.retrbinary(f"RETR {filename}", bio.write)
            bio.seek(0)
            return send_file(bio, as_attachment=True, download_name=os.path.basename(filename))
    except ftplib.error_perm:
        return abort(404)
    finally:
        ftp.quit()

if __name__ == '__main__':
    app.run(host= "0.0.0.0" , port=50110, debug=True)  