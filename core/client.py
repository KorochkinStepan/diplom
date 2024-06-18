import datetime
import socket
import json
import time
import os
import os
from pathlib import Path
import win32clipboard as clipboard
import win32clipboard
from PIL import ImageGrab
import easyocr
import docx2txt
from pypdf import PdfReader
import pandas as pd
import json
from dotenv import load_dotenv
import watchdog.observers
import watchdog.events
import json
import uuid
import os
from pathlib import Path
from elasticsearch import Elasticsearch
import win32clipboard
from utils import (
    create_index_with_mapping,
    search_all_files,
    get_clipboard_content_type_and_hash,
    get_file_size,
    easyocr_recognition,
    parse_date
)
from threading import Thread

import logging
logger = logging.getLogger()

# INITIALIZING ENV
load_dotenv()
HOST = os.environ.get("ELASTIC_HOST")
CLIENT_ID = f"user_{str(uuid.getnode())}"
client_name = os.environ.get("CLIENT_NAME", CLIENT_ID)
EXTENSIONS = json.loads(os.environ.get("EXTENSIONS"))
DIRECTORY = os.environ.get("DIRECTORY_PATH", "./")

user_files_index = os.environ.get("USER_FILES_INDEX", "files")
user_clipboards_index = os.environ.get("USER_CLIPBOARD_INDEX", "clipboard")

# Initialize Elasticsearch client
try:
    es = Elasticsearch(HOST)
except Exception as e:
    logger.error(f"error while connect to Elastic {e.__str__()}")



def send_clipboard_data(data_type, data):
    print(f'sended {data}')
    doc = {
        'data_type': data_type,
        'content': data,
        'client_id': CLIENT_ID,
        'client_name': client_name,
        'time': parse_date(f'{datetime.datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}'),
    }
    es.index(index=user_clipboards_index, body=doc)


def clipboard_monitoring():
    last_clipboard_data = (None, None)

    while True:
        try:
            current_clipboard_data = get_clipboard_content_type_and_hash()
        except Exception as e:
            print(f"Error accessing clipboard: {e}")
            current_clipboard_data = (None, None, None)

        if current_clipboard_data[1] != last_clipboard_data:
            if current_clipboard_data[0] == "image":
                current_clipboard_data[2].save(f'{CLIENT_ID}.png')
                img_data = easyocr_recognition(f'{CLIENT_ID}.png')
                send_clipboard_data('image', img_data)
                last_clipboard_data = current_clipboard_data[1]
            else:
                last_clipboard_data = current_clipboard_data[1]
                send_clipboard_data('text', current_clipboard_data[2])

        time.sleep(1)  # Проверять буфер обмена каждую секунду

class FileEventHandler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=EXTENSIONS,
                                                             ignore_directories=True,
                                                             case_sensitive=False)
        self.es = es
        self.index = user_files_index

    def on_created(self, event):
        print('on_created used')
        if event.is_directory:
            return
        file_path = event.src_path
        base, ext = os.path.splitext(file_path)
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
                'file_path': event.src_path,
                'content': content,
                'client_id': CLIENT_ID,
                'client_name': client_name,
                'file_name': Path(event.src_path).name,
                'extension': Path(event.src_path).suffix,
                'time': parse_date(f'{datetime.datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}'),
                'file_size': get_file_size(event.src_path)
            }
            self.es.index(index=self.index, body=doc)
        file_path = event.src_path
        logger.debug(f"File created: {file_path}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.es.delete_by_query(index=self.index,
                                body={"query": {"match": {"file_path":
                                                              event.src_path}}})
        logger.debug(f"File deleted: {event.src_path}")

    def on_modified(self, event):
        file_path = event.src_path
        base, ext = os.path.splitext(file_path)
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
            'file_path': event.src_path,
            'content': content,
            'client_id': CLIENT_ID,
            'client_name': client_name,
            'file_name': Path(event.src_path).name,
            'extension': Path(event.src_path).suffix,
            'time': parse_date(f'{datetime.datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}'),
            'file_size': get_file_size(event.src_path)
        }
        self.es.index(index=self.index, body=doc)
        logger.debug(f"File modified: {event.src_path}")


try:
    create_index_with_mapping(es, user_files_index)
    logger.debug(f"[INFO] FILES INDEX IS CREATED")
    logger.debug(f"[INFO] FILES INDEX IS CREATED")
    create_index_with_mapping(es, user_clipboards_index)
    logger.debug(f"[INFO] CLIPBOARD INDEX IS CREATED")
    logger.debug(f"[INFO] CLIPBOARD INDEX IS CREATED")


except Exception as e:
    logger.warning(e.__str__())
    logger.debug(f"[INFO] CLIPBOARD OR FILES INDEX IS ALREARY CREATED")
    pass  # TODO

search_all_files(es,
                 index=user_files_index,
                 directory=DIRECTORY,
                 extensions=EXTENSIONS,
                 CLIENT_ID=CLIENT_ID,
                 client_name=client_name)
thread = Thread(target=clipboard_monitoring, daemon=True)
thread.start()

logger.debug('Clipboard Thread is started ')

event_handler = FileEventHandler()
observer = watchdog.observers.Observer()
observer.schedule(event_handler, DIRECTORY, recursive=True)
observer.start()
logger.debug("Observer is started")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    observer.join()
    thread.join()
