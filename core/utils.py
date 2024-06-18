import hashlib
import os
from datetime import datetime
from pathlib import Path
import win32clipboard as clipboard
import win32clipboard
from PIL import ImageGrab
import easyocr
import docx2txt
from pypdf import PdfReader
import pandas as pd

def create_index_with_mapping(es, index_name):
  mapping = {
      "mappings": {
          "properties": {
              "file_path": {"type": "keyword"},
              "content": {"type": "text", "fielddata": True}  # Enable fielddata for text field
          }
      }
  }
  es.indices.create(index=index_name, body=mapping)

def parse_date(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")

# Function to index files in Elasticsearch
def search_all_files(es, index, directory, extensions, CLIENT_ID, client_name):
    extensions = [ext[1:] for ext in extensions]
    for root, dirs, files in os.walk(directory):
        for file in files:
            base, ext = os.path.splitext(file)
            if ext in extensions:
                file_path = os.path.join(root, file)
            if ext == '.docx' or ext == '.doc':
                content = docx2txt.process(file_path)
            elif ext == '.csv':
                content = pd.read_csv(file_path).__str__()
            elif ext == ".xlsx" or ext == ".xls":
                content = pd.read_excel(file_path).__str__()
            elif ext == ".pdf":
                page_content = []
                reader = PdfReader(file_path)
                for page in reader.pages:
                    page_content.append(page.extract_text())
                content = " ".join(page_content)
            else:
                with open(file_path, 'r', encoding="utf-8") as file_content:
                    content = file_content.read()
            doc = {
                'file_path': file_path,
                'content': content,
                'client_id': CLIENT_ID,
                'client_name': client_name,
                'file_name': Path(file_path).name,
                'extension': Path(file_path).suffix,
                'time': parse_date(f'{datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}'),
                'file_size': get_file_size(file_path)
            }
            print(f"send {file_path}to ELASTIC EHEHE")
            es.index(index=index, body=doc)


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def get_file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

import traceback
import win32clipboard as clipboard
import time
import hashlib
from PIL import ImageGrab

import traceback


def send_data(data_type, data_hash, data_content):
    print(f"Data type: {data_type}")
    print(f"Data hash: {data_hash}")
    print(f"Data content: {data_content}")


def get_clipboard_content_type_and_hash():
    clipboard.OpenClipboard()

    try:
        # Проверка на наличие текста в буфере обмена
        if clipboard.IsClipboardFormatAvailable(clipboard.CF_UNICODETEXT):
            data = clipboard.GetClipboardData(clipboard.CF_UNICODETEXT)
            data_type = 'text'
            data_hash = hashlib.md5(data.encode('utf-8')).hexdigest()
            data_content = data
            clipboard.CloseClipboard()
        # Проверка на наличие изображения в буфере обмена
        elif clipboard.IsClipboardFormatAvailable(clipboard.CF_BITMAP):
            image = ImageGrab.grabclipboard()
            if image is not None:
                data_type = 'image'
                data_hash = hashlib.md5(image.tobytes()).hexdigest()
                data_content = image
            else:
                data_type = 'unknown'
                data_hash = None
                data_content = None

        else:
            data_type = 'unknown'
            data_hash = None
            data_content = None
    except Exception as e:
        print(e.__str__())
        traceback.print_exc()


    return data_type, data_hash, data_content

def easyocr_recognition(path_img):
    return easyocr.Reader(["ru"]).readtext(path_img, detail=0, paragraph=True, text_threshold=0.8)



