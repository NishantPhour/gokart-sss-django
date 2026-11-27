from django.core.management.base import BaseCommand
import requests
from django import conf
from django.core.cache import cache
from sss import models
from sss import spatial_tile_cache
import os, errno
import time
from django.utils import timezone
import json
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger('cron_tasks')

class Command(BaseCommand):
    help = 'Purge expired spatial tile cache'
    command_name = 'purge_expired_spatial_cache'

    def handle(self, *args, **kwargs):
        start_time = timezone.now()
        if conf.settings.SPATIAL_TILE_CACHE_BLOB:
            spatial_tile_cache.purge_expired_blob_cache()
            return
        try:
         
            json_files = []
            for root, _, files in os.walk(conf.settings.SPATIAL_TILE_CACHE_DIR, topdown=True):
                for fname in files:
                    if fname.lower().endswith('.json'):
                                                
                        json_file = os.path.join(root, fname)

                        with open(json_file, "r", encoding="utf-8") as file:
                            try:
                                data = json.load(file)

                                if 'status_code' in data and 'cache_expiry' in data and 'current_date_time' in data:                                    
                                    current_date_time = data["current_date_time"]
                                    cache_expiry = data["cache_expiry"]
                                    cache_creation_dt = datetime.strptime(current_date_time, "%Y-%m-%d %H:%M:%S")
                                    
                                    now = datetime.now()
                                    diff = now - cache_creation_dt
                                    in_seconds = diff.seconds
                                    if in_seconds > cache_expiry:    
                                        print ("Cache expired with expiry {} calculated at {} ".format(cache_expiry,in_seconds))                                
                                        if os.path.exists(json_file):
                                            os.remove(json_file)
                                            print(f"File '{json_file}' has been deleted.")
                                        else:
                                            print(f"File '{json_file}' does not exist.")

                            except Exception as e:
                                print (e)
# {
#     "status_code": 200,
#     "content_type": "image/png",
#     "cache_expiry": 300,
#     "browser_cache_expiry": 300,
#     "current_date_time": "2025-12-02 14:29:05"
# }


            # print (json_files)
   
            
        except Exception as e:
            logger.error(f"Failed to access database for command status: {e}")
            return
        