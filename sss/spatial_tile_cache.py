from django import conf
from datetime import datetime
import hashlib
import struct
import os
import json
import threading


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
    SPATIAL_TILE_CACHE_DIR = conf.settings.SPATIAL_TILE_CACHE_DIR
    hashkey = generate_hash_key(unique_key)
    first_dir = hashkey[0:1]
    second_dir = hashkey[0:2]
    folder_path=SPATIAL_TILE_CACHE_DIR+"/"+cache_folder+"/"+first_dir+"/"+second_dir+"/"
    
    file_path=hashkey+".txt"
    if "image/png" in meta_data["content_type"]:
        file_path=hashkey+".png"
    if "image/jpeg" in meta_data["content_type"]:
        file_path=hashkey+".jpg"
    if "application/json" in meta_data["content_type"]:
        file_path=hashkey+".json"
        

    meta_data_file_path = hashkey+"-meta.json"
    os.makedirs(folder_path, exist_ok=True)
    write_data_to_binary_file(folder_path+file_path,data)
    write_meta_data(folder_path+meta_data_file_path, meta_data)
    return folder_path+file_path


def get_cache(cache_folder, unique_key):
    SPATIAL_TILE_CACHE_DIR = conf.settings.SPATIAL_TILE_CACHE_DIR
    hashkey = generate_hash_key(unique_key)
    first_dir = hashkey[0:1]
    second_dir = hashkey[0:2]
    folder_path=SPATIAL_TILE_CACHE_DIR+"/"+cache_folder+"/"+first_dir+"/"+second_dir+"/"
    
    meta_data = get_meta_data(cache_folder, unique_key)
    
    file_path=hashkey+".txt"
    

    if meta_data:
        if "image/png" in meta_data["content_type"]:
            file_path=hashkey+".png"
        if "image/jpeg" in meta_data["content_type"]:
            file_path=hashkey+".jpg"
        if "application/json" in meta_data["content_type"]:
            file_path=hashkey+".json"

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
            
    if os.path.exists(folder_path+file_path):                        
        return folder_path+file_path
        # return read_binary_file(folder_path+file_path)
    else:        
        return None

def get_meta_data(cache_folder, unique_key):
    SPATIAL_TILE_CACHE_DIR = conf.settings.SPATIAL_TILE_CACHE_DIR
    hashkey = generate_hash_key(unique_key)
    first_dir = hashkey[0:1]
    second_dir = hashkey[0:2]
    folder_path=SPATIAL_TILE_CACHE_DIR+"/"+cache_folder+"/"+first_dir+"/"+second_dir+"/"
    file_path=hashkey+"-meta.json"
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
     