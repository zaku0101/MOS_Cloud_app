from flask import Flask
from flask import *
from flask import render_template,send_file, abort
from pathlib import Path
import shutil, os, datetime, random
import datetime as dt

app = Flask(__name__, static_folder="static", template_folder="template")

basePath = r'/Users/zaku/Desktop/mos-drive'

@app.route('/')
def dupa1():
    return render_template("index.html")

def getReadableByteSize(num, suffix='B') -> str:
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def getTimeStampString(tSec: float) -> str:
    tObj = dt.datetime.fromtimestamp(tSec)
    tStr = dt.datetime.strftime(tObj, '%Y-%m-%d %H:%M:%S')
    return tStr
def getIconClassForFilename(fName):
    fileExt = Path(fName).suffix
    fileExt = fileExt[1:] if fileExt.startswith(".") else fileExt
    fileTypes = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg", "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql", "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    fileIconClass = f"bi bi-filetype-{fileExt}" if fileExt in fileTypes else "bi bi-file-earmark"
    return fileIconClass


@app.route('/drive/' ,defaults={'reqPath' : ''})
@app.route('/drive/<path:reqPath>')
def getFiles(reqPath):
    
    absPath = os.path.join(basePath, reqPath)
    
    if not os.path.exists(absPath):
        return abort(404)
    
    if os.path.isfile(absPath):
        return send_file(absPath)
    
    def fObjFromScan(x):
        fileStat = x.stat()
        return{'name' : x.name,
               'fIcon': "bi bi folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
               'relPath' : os.path.relpath(x.path, basePath).replace("\\","/"),
               'mTime':getTimeStampString(fileStat.st_mtime),
               'size':getReadableByteSize(fileStat.st_size)}
    fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]

    return render_template('drive.html.j2' , data={
        'files': fileObjs})   


app.run(host= "0.0.0.0" , port=50100, debug=True)  