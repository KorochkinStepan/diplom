import os
from datetime import datetime
from pathlib import Path

import win32clipboard


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


def get_clipboard_data():
    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    return data