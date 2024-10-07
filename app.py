from flask import Flask
from flask import *
from flask import render_template,send_file, abort
from pathlib import Path
import shutil, os, datetime, random
import datetime as dt

app = Flask(__name__, static_folder="static", template_folder="template")

base_path = r'/Users/zaku/Desktop/mos-drive'

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
    
    abs_path = os.path.join(base_path, req_path)
    
    if not os.path.exists(abs_path):
        return abort(404)
    
    if os.path.isfile(abs_path):
        return send_file(abs_path)
    
    def fobj_from_scan(x):
        file_stat = x.stat()
        return{'name' : x.name,
               'fIcon': "bi bi folder-fill" if False else get_icon_class_for_filename(x.name),
               'relPath' : os.path.relpath(x.path, base_path).replace("\\","/"),
               'mTime':get_time_stamp_string(file_stat.st_mtime),
               'size':get_readable_byte_size(file_stat.st_size)}
    file_objs = [fobj_from_scan(x) for x in os.scandir(abs_path)]

    return render_template('drive2.html' , data={
        'files': file_objs})   

if __name__ == '__main__':
    app.run(host= "0.0.0.0" , port=50100, debug=True)  