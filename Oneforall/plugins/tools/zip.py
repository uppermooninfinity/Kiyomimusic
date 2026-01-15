import pyzipper
import os
from zipfile import ZipFile

def zip_file(file_path):
    zip_path = file_path + ".zip"
    with ZipFile(zip_path, 'w') as zipf:
        zipf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path

def zip_with_password(file_path, password):
    zip_path = file_path + ".zip"
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(password.encode())
        zf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path

def zip_multiple_files(file_paths: list, zip_name='archive.zip'):
    zip_path = os.path.join("/tmp", zip_name)
    with ZipFile(zip_path, 'w') as zipf:
        for file_path in file_paths:
            zipf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path