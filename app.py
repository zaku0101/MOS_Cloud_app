from flask import Flask
from flask import *
from flask import render_template,send_file, abort
from pathlib import Path
import shutil, os, datetime, random
import datetime as dt
import ftplib
import io

app = Flask(__name__, static_folder="static", template_folder="template")
app.secret_key = os.urandom(24)

FTP_HOST = "localhost"



def get_ftp_connection():
    ftp = ftplib.FTP(FTP_HOST)
    if 'username' in session and 'password' in session:
        ftp.login(session['username'], session['password'])
    else:
        ftp.login()
    return ftp

@app.route('/')
def main_page():
    ftp=get_ftp_connection()
    ftp.close()
    return render_template("index.html")

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(username, password)
        session['username'] = username
        session['password'] = password
        
        return redirect(url_for('get_files', req_path=''))
    except ftplib.error_perm:
        flash('Invalid login/password', 'error')
        return redirect(url_for('main_page'))

@app.route('/guest_login')
def guest_login():
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('get_files', req_path=''))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('main_page'))


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
    if 'username' in session and 'password' in session:
        return render_template('drive_logged.html', data={'files': file_objs, 'parentFolder': parent_folder, 'extraOptions': True})
    else:
        return render_template('drive.html', data={'files': file_objs, 'parentFolder': parent_folder})


@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    ftp = get_ftp_connection()
    try:
        # Check if the path is a directory
        try:
            ftp.cwd(filename)
            flash(f'{filename} is a directory, cannot download.', 'error')
            return redirect(url_for('get_files', req_path=filename))
        except ftplib.error_perm:
            # If changing directory fails, it means it's a file
            pass

        bio = io.BytesIO()
        ftp.retrbinary(f"RETR {filename}", bio.write)
        bio.seek(0)
        return send_file(bio, as_attachment=True, download_name=os.path.basename(filename))
    except ftplib.error_perm as e:
        flash(f'Failed to download {filename}: {e}', 'error')
        return redirect(url_for('get_files', req_path=os.path.dirname(filename)))
    except Exception as e:
        flash(f'An unexpected error occurred: {e}', 'error')
        return redirect(url_for('get_files', req_path=os.path.dirname(filename)))
    finally:
        ftp.quit()


def is_directory(ftp, path):
    try:
        original_cwd = ftp.pwd()
        ftp.cwd(path)
        ftp.cwd(original_cwd)
        return True
    except ftplib.error_perm:
        return False

@app.route('/delete/<path:filename>', methods=['GET'])
def delete_file(filename):
    ftp = get_ftp_connection()
    try:
        if is_directory(ftp, filename):
            ftp.rmd(filename)
        else:
            ftp.delete(filename)
        flash(f'File {filename} deleted successfully', 'success')
    except ftplib.error_perm:
        flash(f'Failed to delete {filename}', 'error')
    return redirect(url_for('get_files', req_path=os.path.dirname(filename)))

@app.route('/upload', methods=['POST'])
def upload_file():
    ftp = get_ftp_connection()
    current_path = request.form.get('current_path', '')

    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    try:
        # Change to the current directory
        ftp.cwd(current_path)
        ftp.storbinary(f'STOR {file.filename}', file.stream)
        flash(f'File {file.filename} uploaded successfully', 'success')
    except ftplib.error_perm:
        flash(f'Failed to upload {file.filename}', 'error')
    finally:
        ftp.quit()
    
    return redirect(url_for('get_files', req_path=current_path))

@app.route('/create_directory', methods=['POST'])
def create_directory():
    ftp = get_ftp_connection()
    data = request.get_json()
    dir_name = data.get('directory_name')
    current_path = data.get('current_path')
    
    print(current_path)
    print(dir_name)
    print(current_path +"/"+ dir_name)
    
    if dir_name:
        try:
            if current_path =="": 
                ftp.mkd(dir_name)
            else:
                ftp.mkd(current_path +"/"+ dir_name)
            return jsonify({"message": "Directory created successfully!"}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 500
    return jsonify({"message": "Invalid directory name."}), 400

if __name__ == '__main__':
    app.run(host= "0.0.0.0" , port=5000, debug=True)
