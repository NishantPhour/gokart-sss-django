from django import conf
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from django.core.exceptions import ImproperlyConfigured
import hashlib
import struct
import os
import json
import threading


@lru_cache(maxsize=1)
def _blob_container(connection_string, container_name):
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient.from_connection_string(connection_string).get_container_client(container_name)


def _get_blob_container():
    connection_string = conf.settings.AZURE_STORAGE_CONNECTION_STRING
    container_name = conf.settings.AZURE_STORAGE_CONTAINER
    if not connection_string or not container_name:
        raise ImproperlyConfigured(
            "SPATIAL_TILE_CACHE_BLOB requires AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER."
        )
    return _blob_container(connection_string, container_name)


def _cache_folder_path(cache_folder, hashkey):
    if conf.settings.SPATIAL_TILE_CACHE_BLOB:
        root = "sss/{}/spatial_tile_cache".format(conf.settings.ENV_TYPE.lower())
    else:
        root = conf.settings.SPATIAL_TILE_CACHE_DIR
    return root + "/" + cache_folder + "/" + hashkey[0:1] + "/" + hashkey[0:2] + "/"


def _cache_file_name(hashkey, meta_data):
    extension = ".txt"
    if "image/png" in meta_data["content_type"]:
        extension = ".png"
    if "image/jpeg" in meta_data["content_type"]:
        extension = ".jpg"
    if "application/json" in meta_data["content_type"]:
        extension = ".json"
    return hashkey + extension


def _read_blob(blob_name):
    from azure.core.exceptions import ResourceNotFoundError

    try:
        return _get_blob_container().download_blob(blob_name).readall()
    except ResourceNotFoundError as error:
        if getattr(error, "error_code", None) == "BlobNotFound":
            return None
        raise


def open_cache(cache_path):
    if conf.settings.SPATIAL_TILE_CACHE_BLOB:
        return BytesIO(_get_blob_container().download_blob(cache_path).readall())
    return open(cache_path, 'rb')


def purge_expired_blob_cache():
    from azure.core.exceptions import ResourceNotFoundError

    container = _get_blob_container()
    prefix = "sss/{}/spatial_tile_cache/".format(conf.settings.ENV_TYPE.lower())
    for blob in container.list_blobs(name_starts_with=prefix):
        if not blob.name.endswith("-meta.json"):
            continue
        raw_metadata = _read_blob(blob.name)
        if raw_metadata is None:
            continue
        meta_data = json.loads(raw_metadata)
        created = datetime.strptime(meta_data["current_date_time"], "%Y-%m-%d %H:%M:%S")
        if int(datetime.now().timestamp()) - int(created.timestamp()) > int(meta_data["cache_expiry"]):
            hash_path = blob.name[:-len("-meta.json")]
            tile_path = _cache_file_name(hash_path, meta_data)
            # A missing tile is expected if another purge has already removed it.
            for path in (tile_path, blob.name):
                try:
                    container.delete_blob(path)
                except ResourceNotFoundError as error:
                    if getattr(error, "error_code", None) != "BlobNotFound":
                        raise


def generate_hash_key(input_string):
    """
    Generates a SHA-256 hexadecimal hash key from an input string.

    Args:
        input_string (str): The string to be hashed.

    Returns:
        str: A 64-character hexadecimal hash key.
    """
    # 1. Encode the string to bytes (required by hash functions)
    encoded_data = input_string.encode('utf-8')

    # 2. Create the SHA-256 hash object and update it with the data
    hash_object = hashlib.sha256(encoded_data)

    # 3. Get the final hexadecimal representation (the key)
    hash_key = hash_object.hexdigest()

    return hash_key

def _atomic_write(filename, data, mode):
    # Write to a unique temp file then rename, so concurrent readers never see a partially written file
    tmp_filename = "{}.{}.{}.tmp".format(filename, os.getpid(), threading.get_ident())
    with open(tmp_filename, mode) as f:
        f.write(data)
    os.replace(tmp_filename, filename)

def write_meta_data(filename, json_data):
    _atomic_write(filename, json.dumps(json_data, indent=4), "w")
    # print("JSON file has been created successfully!")

def write_data_to_file(filename, data):

    # Write JSON to a file
    with open(filename, "w") as file:
        f.write(data)

def write_data_to_binary_file(filename, binary_data):
    """
    Writes various types of binary data (bytes, packed integers, and a float)
    to a specified file.
    """
    print(f"--- Starting to write binary data to '{filename}' ---")

    try:
        _atomic_write(filename, binary_data, 'wb')
        file_size = os.path.getsize(filename)
        # print(f"--- Successfully wrote to file. Total file size: {file_size} bytes. ---")

    except IOError as e:
        print(f"An error occurred while writing the file: {e}")


# Optional: Add a function to read the data back to demonstrate the raw bytes
def read_binary_file(filename):
    """
    Reads and prints the raw binary content of the file.
    """
    # print(f"\n--- Reading raw binary content from '{filename}' ---")
    raw_content_mem = b''
    try:
        with open(filename, 'rb') as f:
            # Read the entire raw content as a bytes object
            raw_content = f.read()
            raw_content_mem = raw_content_mem + raw_content
            # print(raw_content)            
        return raw_content_mem  
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")

def read_json_file(filename):
  
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def read_data_file(filename):
  
    with open(filename, 'r') as file:
        data = file.read()
    return data

def set_cache(cache_folder, unique_key, data, cache_expiry, meta_data):
    hashkey = generate_hash_key(unique_key)
    folder_path = _cache_folder_path(cache_folder, hashkey)
    file_path = _cache_file_name(hashkey, meta_data)

    meta_data_file_path = hashkey+"-meta.json"
    if conf.settings.SPATIAL_TILE_CACHE_BLOB:
        container = _get_blob_container()
        container.upload_blob(folder_path+file_path, data, overwrite=True)
        container.upload_blob(
            folder_path+meta_data_file_path,
            json.dumps(meta_data, indent=4).encode('utf-8'),
            overwrite=True,
        )
    else:
        os.makedirs(folder_path, exist_ok=True)
        write_data_to_binary_file(folder_path+file_path,data)
        write_meta_data(folder_path+meta_data_file_path, meta_data)
    return folder_path+file_path


def get_cache(cache_folder, unique_key):
    hashkey = generate_hash_key(unique_key)
    folder_path = _cache_folder_path(cache_folder, hashkey)
    
    meta_data = get_meta_data(cache_folder, unique_key)
    
    if meta_data:
        file_path = _cache_file_name(hashkey, meta_data)

        if "current_date_time" in meta_data:            
            dt = datetime.strptime(meta_data["current_date_time"], "%Y-%m-%d %H:%M:%S")
            epoch_time = int(dt.timestamp())

            now = datetime.now()
            now_epoch = int(now.timestamp())
            difference = now_epoch - epoch_time

            # print(f"Epoch time from JSON: {epoch_time}")
            # print(f"Current epoch time: {now_epoch}")
            # print(f"Difference in seconds: {difference}")
        else:                     
            return None
    else:                
        return None

    if difference > int(meta_data["cache_expiry"]):
        print ("expired : {}".format(unique_key))          
        return None
            
    if conf.settings.SPATIAL_TILE_CACHE_BLOB:
        from azure.core.exceptions import ResourceNotFoundError

        try:
            _get_blob_container().get_blob_client(folder_path+file_path).get_blob_properties()
            exists = True
        except ResourceNotFoundError as error:
            if getattr(error, "error_code", None) != "BlobNotFound":
                raise
            exists = False
    else:
        exists = os.path.exists(folder_path+file_path)
    if exists:
        return folder_path+file_path
        # return read_binary_file(folder_path+file_path)
    else:        
        return None

def get_meta_data(cache_folder, unique_key):
    hashkey = generate_hash_key(unique_key)
    folder_path = _cache_folder_path(cache_folder, hashkey)
    file_path=hashkey+"-meta.json"
    if conf.settings.SPATIAL_TILE_CACHE_BLOB:
        raw_metadata = _read_blob(folder_path+file_path)
        return json.loads(raw_metadata) if raw_metadata is not None else None
    if os.path.exists(folder_path+file_path):
        
        return read_json_file(folder_path+file_path)        
        # return read_binary_file(folder_path+file_path)
    else:
        return None

def file_iterator(file_name, chunk_size=8192):
    
    with open(file_name, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def file_iterator_plain(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            yield line
     