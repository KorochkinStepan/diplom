import os
import time
import json
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import logging
logger = logging.getLogger()
load_dotenv()
# Initialize Elasticsearch client
HOST = os.environ.get("ELASTIC_HOST")
try:
    es = Elasticsearch(HOST)
except Exception as e:
    logger.error(f"error while connect to Elastic {e.__str__()}")
print(os.environ.get("SENSITIVE_INFO_LIST"))
print(os.environ.get("EXTENSIONS"))
keys_list = json.loads(os.environ.get("SENSITIVE_INFO_LIST")) #["ФИО", "Адрес", "Дата Рождения"]
# Define index names
user_files_index = os.environ.get("USER_FILES_INDEX", "files")
user_clipboards_index = os.environ.get("USER_CLIPBOARD_INDEX", "clipboard")
data_leaks_files_index = os.environ.get("DATA_LEAKS_FILES_INDEX", "data_leaks_files")
data_leaks_clipboards_index = os.environ.get("DATA_LEAKS_CLIPBOARD_INDEX", "data_leaks_clipboards")

leaks_mapping = {user_files_index: data_leaks_files_index,
                 user_clipboards_index: data_leaks_clipboards_index}
# Function to iterate over documents in an index and process them



# Function to search for sensitive data in a file using Elasticsearch
def search_keys_in_documents(index, keys_list):
    for key in keys_list:
        query = {
            "query": {
                "match": {
                    "content": key
                }
            }
        }
        res = es.search(index=index, body=query, _source=True)  # Retrieving the source document
        if res['hits']['total']['value'] > 0:
            logger.debug(f"Key '{key}' found in documents.")
            deleted = []
            for hit in res['hits']['hits']:

                # Creating a new document in the "leak" index

                es.index(index=leaks_mapping[index], body=hit['_source'])
                if hit['_id'] not in deleted:
                    es.delete(index=index, id=hit['_id'])
                    deleted.append(hit['_id'])

        else:
            logger.debug(f"Key '{key}' not found in documents.")

    must_not_clauses = [{"match": {"content": keyword}} for keyword in keys_list]
    # Construct the Elasticsearch query
    query = {
        "query": {
            "bool": {
                "must_not": must_not_clauses
            }
        }
    }
    # Search for documents not matching the criteria
    res = es.search(index=index, body=query, _source=False)

    for hit in res['hits']['hits']:
        logger.debug(hit, hit['_id'])
        # Delete documents not matching the criteria
        es.delete(index=index, id=hit['_id'])


def create_index_with_mapping(index_name):
    mapping = {
        "mappings": {
            "properties": {
                "file_path": {"type": "keyword"},
                "content": {"type": "text", "fielddata": True}  # Enable fielddata for text field
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)

# Main function
if __name__ == "__main__":
    try:
        create_index_with_mapping(user_files_index)
    except Exception as e:
        print(f"{user_files_index} already exists")
        logger.debug(f"{user_files_index} already exists")
    try:
        create_index_with_mapping(user_clipboards_index)
    except Exception as e:
        logger.debug(f"{user_clipboards_index} already exists")
    try:
        create_index_with_mapping(data_leaks_files_index)
    except Exception as e:
        logger.debug(f"{data_leaks_files_index} already exists")
    try:
        create_index_with_mapping(data_leaks_clipboards_index)
    except Exception as e:
        logger.debug(f"{data_leaks_clipboards_index} already exists")

    while True:
        time.sleep(3)
        search_keys_in_documents(user_files_index, keys_list)
        search_keys_in_documents(user_clipboards_index, keys_list)
