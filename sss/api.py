from django.http import HttpResponse, JsonResponse, Http404,StreamingHttpResponse
from django import conf
from django.views.decorators.csrf import csrf_exempt
from wagov_utils.components.proxy.views import proxy_view
from django.core.cache import cache
from django.template.loader import render_to_string
from django.shortcuts import render 
from django.db.models import Q, Max
from django.contrib.auth.models import User
from requests.auth import HTTPBasicAuth
from sss import raster
from sss import sss_gdal
from sss import spatial as sss_spatial
import shutil
import os 
import requests
import base64
import datetime
import ast
import json
import logging
import pathlib
import re
from io import BytesIO
from urllib.parse import urlsplit
from sss.models import UserProfile, Proxy, MapServer, SpatialDataCalculation
from sss import models as sss_models
from sss.serializers import ProfileSerializer, AccountDetailsSerializer
from django.http import FileResponse, Http404, HttpResponseForbidden
import mimetypes
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from sss import utils_cache
from django.conf import settings
from jinja2 import Template, Environment, FileSystemLoader
from django.core.exceptions import ObjectDoesNotExist
from sss.models import ManagementCommandStatus
from django.utils import timezone
from datetime import timedelta
from sss import spatial_tile_cache

logger = logging.getLogger("log")

def api_catalogue(request, *args, **kwargs):
    if request.user.is_authenticated:

        # if DEV use this
        # file = open(str(conf.settings.BASE_DIR)+"/devdata/catalogue.json", "r")
        # data = file.read()
        # file.close()

        catalogue_cache_dumped_data =cache.get('catalogue_cache_data')
        catalogue_data = None

        if catalogue_cache_dumped_data is None:
            catalogue_url = conf.settings.CATALOGUE_URL+"/catalogue/api/records/?format=json&application__name=sss"    
            auth_request = requests.auth.HTTPBasicAuth(conf.settings.AUTH2_BASIC_AUTH_USER, conf.settings.AUTH2_BASIC_AUTH_PASSWORD)
            response = requests.get(catalogue_url, auth=auth_request)
            catalogue_data  = response.text
            if response.status_code == 200:
                cache.set('catalogue_cache_data', catalogue_data, 86400)
            
        else:
            catalogue_data =  catalogue_cache_dumped_data

        return HttpResponse(catalogue_data, content_type='application/json')
    else:
        raise ValidationError('User is not authenticated')
    
def api_bfrs_region(request, *args, **kwargs):
    if request.user.is_authenticated:

        # if DEV use this
        # file = open(str(conf.settings.BASE_DIR)+"/devdata/catalogue.json", "r")
        # data = file.read()
        # file.close()

        bfrs_region_cache_dumped_data =cache.get('bfrs_region_cache_data')
        bfrs_region_data = None

        if bfrs_region_cache_dumped_data is None:
            bfrs_region_url = conf.settings.BFRS_URL+"/api/v1/region/?format=json"
            auth_request = requests.auth.HTTPBasicAuth(conf.settings.AUTH2_BASIC_AUTH_USER, conf.settings.AUTH2_BASIC_AUTH_PASSWORD)
            response = requests.get(bfrs_region_url, auth=auth_request)
            bfrs_region_data  = response.text
            if response.status_code == 200:
                cache.set('bfrs_region_cache_data', bfrs_region_data, 86400)
            
        else:
            bfrs_region_data =  bfrs_region_cache_dumped_data

        return HttpResponse(bfrs_region_data, content_type='application/json')
    else:
        raise ValidationError('User is not authenticated')
    

# @csrf_exempt
# def kmiProxyView(request, path):
#     # start move to django model
#     # cache_times_strings = [
#     #     {'layer_name': 'mapbox-outdoors',
#     #      'cache_expiry' : 172800
#     #     },
#     #     {'layer_name': 'fuel_age_nonforest_1_6yrs_cddp',
#     #      'cache_expiry' : 300},  
#     #     {'layer_name': 'state_map_base', 
#     #      'cache_expiry' : 172800
#     #     },
#     #     {'layer_name': 'resource_tracking_live', 
#     #      'cache_expiry' : 30
#     #     } 
#     # ]
#     cache_times_strings = utils_cache.get_proxy_cache()
#     # end move to django model
#     CACHE_EXPIRY=300
#     remoteurl = conf.settings.KMI_API_URL + '/' + path   
#     query_string_remote_url=remoteurl+'?'+request.META['QUERY_STRING']
#     proxy_response = None
#     proxy_cache = cache.get(query_string_remote_url)
#     #proxy_cache= None
#     proxy_response_content = None
#     base64_json = {}


#     for cts in cache_times_strings:
#         if cts['layer_name'] in query_string_remote_url:
#             CACHE_EXPIRY = cts['cache_expiry']
#         print (cts['layer_name'])

#     print (CACHE_EXPIRY)
#     if proxy_cache is None:
#         proxy_response = proxy_view(request, remoteurl, basic_auth={"user": conf.settings.KMI_AUTH2_BASIC_AUTH_USER, 'password' : conf.settings.KMI_AUTH2_BASIC_AUTH_PASSWORD}, cookies={})    
#         proxy_response_content_encoded = base64.b64encode(proxy_response.content)
#         base64_json = {"status_code": proxy_response.status_code, "content_type": proxy_response.headers['content-type'], "content" : proxy_response_content_encoded.decode('utf-8'), "cache_expiry": CACHE_EXPIRY}
#         if proxy_response.status_code == 200: 
#             cache.set(query_string_remote_url, json.dumps(base64_json), CACHE_EXPIRY)
#         else:
#             cache.set(query_string_remote_url, json.dumps(base64_json), 15)
#     else:
#         print ("CACHED")
#         print (query_string_remote_url)
#         base64_json = json.loads(proxy_cache)
#     proxy_response_content = base64.b64decode(base64_json["content"].encode())
#     http_response =   HttpResponse(proxy_response_content, content_type=base64_json['content_type'], status=base64_json['status_code'])    
#     http_response.headers['Django-Cache-Expiry']= str(base64_json['cache_expiry']) + " seconds"
#     return http_response



def process_proxy(request, remoteurl, queryString, auth_user, auth_password):
    proxy_cache= None
    proxy_response = None
    proxy_response_content = None
    base64_json = {}

    get_layers_lc = request.GET.get("layers", None)
    get_layer_lc = request.GET.get("layer", None)   
    get_layers_uc = request.GET.get("LAYERS", None) 
    get_typename_lc = request.GET.get("typename", None) 



    spatial_tile_folder = "other"
    if get_layers_lc:
        spatial_tile_folder=get_layers_lc
    if get_layer_lc:
        spatial_tile_folder=get_layer_lc        
    if get_layers_uc:
        spatial_tile_folder=get_layers_uc
    if get_typename_lc:
        spatial_tile_folder=get_typename_lc
    
    query_string_remote_url=remoteurl+'?'+queryString

    cache_times_strings = utils_cache.get_proxy_cache()
    CACHE_EXPIRY=300
    BROWSER_CACHE_EXPIRY = None
    CACHE_STATUS = "MISS"
    current_date_time = datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S")
    # proxy_cache = cache.get(query_string_remote_url)
    proxy_cache = spatial_tile_cache.get_cache(spatial_tile_folder, query_string_remote_url)

    # print (proxy_cache)
    for cts in cache_times_strings:
        if cts['layer_name'] in query_string_remote_url:
            CACHE_EXPIRY = cts['cache_expiry']
            if cts['browser_expiry']:
                BROWSER_CACHE_EXPIRY = cts['browser_expiry']
        #print (cts['layer_name'])
    if BROWSER_CACHE_EXPIRY is None:
        BROWSER_CACHE_EXPIRY = CACHE_EXPIRY
    # proxy_cache = None

    if proxy_cache is None:
        #print ("NO CACHE")
        auth_details = None
        if auth_user is None and auth_password is None:
            auth_details = None
        else:
            auth_details = {"user": auth_user, 'password' : auth_password}
        proxy_response = proxy_view(request, remoteurl, basic_auth=auth_details, cookies={})           
        proxy_response_content_encoded = proxy_response.content
        base64_json = {"status_code": proxy_response.status_code, "content_type": proxy_response.headers['content-type'], "cache_expiry": CACHE_EXPIRY, "browser_cache_expiry": BROWSER_CACHE_EXPIRY,"current_date_time": current_date_time}
        if proxy_response.status_code in (200, 201):
            #print ("CREATING CACHE")
            proxy_cache = spatial_tile_cache.set_cache(spatial_tile_folder,query_string_remote_url,proxy_response.content,CACHE_EXPIRY,base64_json)
        else:
            base64_json["cache_expiry"] = 15
            BROWSER_CACHE_EXPIRY = 15
            proxy_cache = spatial_tile_cache.set_cache(spatial_tile_folder,query_string_remote_url,proxy_response.content,15,base64_json)
            # cache.set(query_string_remote_url, json.dumps(base64_json), 15)
    else:
        
        CACHE_STATUS = "HIT"
        base64_json = spatial_tile_cache.get_meta_data(spatial_tile_folder, query_string_remote_url)
        BROWSER_CACHE_EXPIRY = base64_json.get("browser_cache_expiry", BROWSER_CACHE_EXPIRY)
    
    if proxy_cache[-3:] == 'png' or proxy_cache[-3:] == 'jpg':
        http_response =   StreamingHttpResponse(spatial_tile_cache.file_iterator(proxy_cache), content_type=base64_json['content_type'], status=base64_json['status_code'])        
    else:
        http_response =   StreamingHttpResponse(spatial_tile_cache.file_iterator_plain(proxy_cache), content_type=base64_json['content_type'], status=base64_json['status_code'])        

    http_response.headers['Django-Cache-Expiry'] = str(base64_json['cache_expiry']) + " seconds"
    http_response.headers['Django-Cache-Status'] = CACHE_STATUS
    http_response.headers['Django-Cache-File'] = proxy_cache
    if "current_date_time" in base64_json:
        http_response.headers['Django-Cache-Datetime'] = base64_json["current_date_time"]
    http_response.headers['Cache-Control'] = 'private, max-age=' + str(BROWSER_CACHE_EXPIRY)+', must-revalidate'
    return http_response


def proxy_object(request_path):
    proxy_dict = {}

    if not proxy_dict:
        try:
            proxy = Proxy.objects.get(
                active=True,
                request_path=request_path,
            )
        except Proxy.DoesNotExist:
            raise
        else:
            proxy_dict = {
                "proxy_url": proxy.proxy_url,
                "basic_auth_enabled": proxy.basic_auth_enabled,
                "username": proxy.username,
                "password": proxy.password,
            }
    return proxy_dict



@csrf_exempt
def mapProxyView(request, request_path, path):
    if not request.user.is_authenticated:
        raise ValidationError("User is not authenticated")

    queryString = request.META["QUERY_STRING"]
    username = request.user.username
    auth_user = None
    auth_password = None

    try:
        proxy = proxy_object(request_path)
    except Proxy.DoesNotExist:
        raise Http404(f"No active Proxy entry found for {username} and {request_path}")
    else:
        if proxy.get("basic_auth_enabled"):
            auth_user = proxy.get("username")
            auth_password = proxy.get("password")
        remoteurl = proxy.get("proxy_url") +"/"+ path
    if "//" in urlsplit(remoteurl).path:
        logger.warning(
            "Proxy '%s': upstream URL path contains a double slash (//), "
            "which can cause layer loading errors. "
            "Check Django admin > Proxies > %s > Proxy URL and remove any trailing slash (/). "
            "Also check the Map server URL and request path for duplicate slashes. "
            "Requests 2.34.0+ preserves duplicate leading slashes.",
            request_path,
            request_path,
        )
    response = process_proxy(request, remoteurl, queryString, auth_user, auth_password)

    return response

    


# @csrf_exempt
# def kbProxyView(request, path):
#     remoteurl = conf.settings.KB_API_URL + '/' + path
     
#     proxy_response = None
#     proxy_cache = cache.get(remoteurl+'?'+request.META['QUERY_STRING'])
#     proxy_cache= None
#     proxy_response_content = None
#     base64_json = {}
#     if proxy_cache is None:
#         proxy_response = proxy_view(request, remoteurl, basic_auth={"user": conf.settings.KB_AUTH2_BASIC_AUTH_USER, 'password' : conf.settings.KB_AUTH2_BASIC_AUTH_PASSWORD}, cookies={})    
#         proxy_response_content_encoded = base64.b64encode(proxy_response.content)
#         base64_json = {"content_type": proxy_response.headers['content-type'], "content" : proxy_response_content_encoded.decode('utf-8')}

#         cache.set(remoteurl+'?'+request.META['QUERY_STRING'], json.dumps(base64_json), 86400)
#     else:
#         # print ("CACHED")
#         # print (remoteurl+'?'+request.META['QUERY_STRING'])
#         base64_json = json.loads(proxy_cache)
#     proxy_response_content = base64.b64decode(base64_json["content"].encode())
#     return HttpResponse(proxy_response_content, content_type=base64_json['content_type'])    

def environment_config(request):
    context = {'settings': conf.settings}
    mapServer = {}
    for object in MapServer.objects.all():
        key = object.name.replace(' ', '_').lower()
        mapServer[key] = object.url
    context['mapserver'] = mapServer
    template_date = render_to_string('sss/environment_config.js', context)   
    return HttpResponse(template_date, content_type='text/javascript')

def cataloguev2(request):
    if request.user.is_authenticated:
        catalogue_array = []
        catalogue = sss_models.Catalogue.objects.filter(active=True)
        for c in catalogue:
            catalogue_row = {}
            catalogue_row['id'] = c.id
            catalogue_row['url'] = c.url
            catalogue_row['identifier'] = c.identifier
            catalogue_row['title'] = c.title
            catalogue_row['workspace'] = c.workspace
            catalogue_row['any_text'] = c.any_text
            catalogue_row['abstract'] = c.abstract
            catalogue_row['keywords'] = c.keywords
            catalogue_row['bounding_box'] = c.bounding_box
            catalogue_row['crs'] = c.crs
            catalogue_row['service_type'] = c.service_type
            catalogue_row['service_type_version'] = c.service_type_version
            if c.legend:
                catalogue_row['legend'] = c.legend
            elif hasattr(c, 'legend_file') and c.legend_file:
                catalogue_row['legend'] = c.legend_file.url
            else:
                catalogue_row['legend'] = None
            catalogue_row['active'] = c.active
            catalogue_row['updated'] = c.updated.strftime("%d/%m/%Y %H:%M:%S")
            catalogue_row['created'] = c.created.strftime("%d/%m/%Y %H:%M:%S")
            catalogue_row['tags'] = []
            catalogue_tags = sss_models.CatalogueTag.objects.filter(catalogue=c)
            catalogue_row['map_server_name'] = c.map_server.name 
            catalogue_row['map_server_url'] = c.map_server.url

            # Fix to add to model tomorrow
            catalogue_row['type'] = "TileLayer"
            if c.type:
                catalogue_row['type'] = c.type
                
            ct_row = {}
            for ct in catalogue_tags:
                ct_row['name'] = ct.name
                ct_row['description'] = ct.description
                catalogue_row['tags'].append(ct_row)

            catalogue_array.append(catalogue_row)


        catalogue_csw = sss_models.CatalogueSyncCSW.objects.filter(active=True, removed_from_csw=False)
        for c_csw in catalogue_csw:
            json_cs_csw = json.loads(c_csw.json_data)
            json_cs_csw['map_server_name'] = "kmi"
            kmi_url = MapServer.objects.get(name='kmi').url
            json_cs_csw['map_server_url'] = kmi_url
            catalogue_array.append(json_cs_csw)

        context = {'settings': conf.settings}
        #template_date = render_to_string('sss/cataloguev2.json', context)    
        return HttpResponse(json.dumps(catalogue_array), content_type='text/json')

def gokart_js(request):
    context = {'settings': conf.settings}
    template_date = render_to_string('sss/gokart.js', context)   
    return HttpResponse(template_date, content_type='text/javascript')

def gokart_client(request):
    context = {'settings': conf.settings}
    response = render(request, 'sss/client.html', context)
    response.headers["X-FRAME-OPTIONS"] = "ALLOWALL"
    return response


def getPrivateFile(request, file_path):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("User is not authenticated")

    private_media_root = settings.PRIVATE_MEDIA_STORAGE_LOCATION
    full_file_path = os.path.join(private_media_root, file_path)

    if not os.path.exists(full_file_path):
        raise Http404("File not found")

    content_type, _ = mimetypes.guess_type(full_file_path)
    if not content_type:
        content_type = "application/octet-stream"
    extension = full_file_path.split(".")[-1].lower()
    if extension in ["msg", "eml"]:
        content_type = "application/vnd.ms-outlook"
    response = FileResponse(open(full_file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(full_file_path)}"'
    return response

def sso_profile(request):
    data= '{"authenticated": true, "email": "test.test@dbca.wa.gov.au", "username": "test.test@dbca.wa.gov.au", "first_name": "Test", "last_name": "Test", "full_name": "Test Test", "groups": "TEST,TEST1,TEST_ADMIN_TEAM,TEST_DEV_TEAM", "logout_url": "/sso/auth_logout", "session_key": "000.000.000.000.000|AUTH2-01|000dddeeefffff|1-auth2018eeedddfffgghhhtttyuuhgg", "auth_cache_hit": "success", "Frame_Options": "DENY", "Content_Type_Options": "nosniff", "client_logon_ip": "000.000.000.000", "access_token": "eeddfffuuiiidlkdldkdkdldkllksdlkdlkkjasdlksajlkdjkhlsajkdsajdlkas", "access_token_created": "2023-07-19 10:24:54", "access_token_expireat": "2023-08-16 23:59:59", "idp": "staff"}'
    return HttpResponse(data, content_type='application/json')

def outlookmetadata(request):

    data = raster.outlookmetadata(request)
    #print ("WEather")
    #print (data)    
    #data = raster.test(request)
    return HttpResponse(json.dumps(data, default=str), content_type='application/json')

@csrf_exempt
def weatheroutlook(request, fmt):
    if request.user.is_authenticated:

        data = raster.weatheroutlook(request, fmt)

        if fmt == 'json':
            content_type = 'application/json'
        elif fmt == 'amicus':
            content_type = 'application/xml'
        elif fmt == 'html':
            content_type = 'text/html'
        else: 
            content_type = 'text/html'
        
        response = HttpResponse(data, content_type=content_type)    
        if fmt == 'json':
            response["Content-Disposition"] = "attachment;filename='weather_outlook_{}.json'".format(datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d_%H%M%S"))
        elif fmt == 'amicus':
            response["Content-Disposition"] = "attachment;filename='weather_outlook_{}.xml'".format(datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d_%H%M%S"))
        return response
    else:
        raise ValidationError('User is not authenticated')

def api_profile(request, *args, **kwargs):
    user_logged_in = None
    if request.user.is_authenticated:
        user_logged_in = request.user
        try:
            user_profile = utils_cache.get_user_profile(user_logged_in, request.session.session_key)
            serializer = ProfileSerializer(user_profile)
            return HttpResponse(json.dumps(serializer.data), content_type='application/json')
        except serializers.ValidationError:
                raise serializers.ValidationError('Serializer not valid')
        except UserProfile.DoesNotExist:
            raise ValidationError('User profile for the logged in user does not exist')
    else:
        raise ValidationError('User is not authenticated')
    
def api_account(request, *args, **kwargs):
    user_logged_in = None
    if request.user.is_authenticated:
        user_logged_in = request.user
        try:
            user_profile = utils_cache.get_user_profile(user_logged_in, request.session.session_key)
            serializer = AccountDetailsSerializer(user_profile)
            return HttpResponse(json.dumps(serializer.data), content_type='application/json')
        except serializers.ValidationError:
                raise serializers.ValidationError('Serializer not valid')
        except UserProfile.DoesNotExist:
            raise ValidationError('User profile for the logged in user does not exist')
    else:
        raise ValidationError('User is not authenticated')
    
def api_mapbox(request, *args, **kwargs):
    if request.user.is_authenticated:

        geo_str = request.GET.get('geo_str')
        country = request.GET.get('country')
        proximity = request.GET.get('proximity')
        access_token = conf.settings.MAPBOX_ACCESS_TOKEN
        mapbox_url = conf.settings.MAPBOX_URL

        params = {
            'country': country,
            'proximity':proximity,
            'access_token': access_token 
        }
        headers = {
            # 'proxy_ssl_server_name': 'on',
            # 'resolver': '127.0.0.0',
            'proxy_set_header': 'Host api.mapbox.com',
            'proxy_hide_header': 'Access-Control-Allow-Credentials',
            'proxy_hide_header': 'Access-Control-Allow-Headers',
            'proxy_hide_header': 'Access-Control-Allow-Methods',
            'proxy_hide_header': 'Access-Control-Allow-Origin',
            'proxy_hide_header': 'Access-Control-Expose-Headers',
            'proxy_hide_header': 'Vary',
            'include': 'custom/cors',
            'proxy_pass': 'https://api.mapbox.com'
        }


        response = requests.get(mapbox_url + '/geocoding/v5/mapbox.places/' + geo_str + '.json', params=params, headers=headers)

        return HttpResponse(response, content_type='application/json')
    else:
        raise ValidationError('User is not authenticated')


@csrf_exempt
def spatial(request):
    if request.user.is_authenticated:
        data = sss_spatial.spatial(request)

        # if fmt == 'json':
        #     content_type = 'application/json'
        # elif fmt == 'amicus':
        #     content_type = 'application/xml'
        # elif fmt == 'html':
        #     content_type = 'text/html'
        # else: 
        #     content_type = 'text/html'
        
        content_type = 'application/json'
        response = HttpResponse(json.dumps(data), content_type=content_type)    
        return response    
    else:
        return HttpResponse('User is not authenticated', content_type='text/plain', status=500)

from django.core.files.uploadedfile import SimpleUploadedFile

@csrf_exempt
def gdal(request, fmt):
    if request.user.is_authenticated:
        print("GENERATING: " + fmt)
        instance_format = settings.EMAIL_INSTANCE + '_'
        # if settings.EMAIL_INSTANCE == "UAT" or settings.EMAIL_INSTANCE == "DEV":
        #     instance_format = settings.EMAIL_INSTANCE + '_'
        
        jpg = request.FILES.get("jpg")
        chunk = request.FILES.get("chunk")
        
        if jpg:
            output_filename = instance_format + jpg.name.replace("jpg", fmt)
            
            if fmt == "tif":
                content_type = "image/tiff"
            elif fmt == "pdf":
                content_type = "application/pdf"                    
            else:
                raise Exception("File format({}) Not Support".format(fmt))
            
            try:
                response = sss_gdal.gdal_convert(request, fmt)
                return response
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        elif chunk:
            start = int(request.POST.get("start"))
            end = int(request.POST.get("end"))
            total_size = int(request.POST.get("totalSize"))
            upload_id = request.POST.get("upload_id")
            workdir = os.path.join(str(settings.BASE_DIR), settings.TEMP_DIR)
            upload_folder = os.path.join(workdir, str(upload_id))
            os.makedirs(upload_folder, exist_ok=True)

            # Create a temp file
            temp_filename = os.path.join(upload_folder, instance_format + "upload_temp_file.jpg")

            # Write the chunk into the file at the correct offset
            with open(temp_filename, 'ab') as temp_file:
                temp_file.seek(start)
                temp_file.write(chunk.read())

            if end >= total_size:
                with open(temp_filename, 'rb') as final_file:
                    merged_jpg = SimpleUploadedFile(name=instance_format + "merged.jpg", content=final_file.read(), content_type='image/jpeg')
                    print('file size')
                    print(os.path.getsize(temp_filename))
                    shutil.rmtree(upload_folder, ignore_errors=True)
                    request.FILES['jpg'] = merged_jpg
                    
                    try:
                        response = sss_gdal.gdal_convert(request, fmt)
                        return response
                    except Exception as e:
                        return JsonResponse({'error': str(e)}, status=500)

            return JsonResponse({"status": "chunk received"})

    else:
        return HttpResponse('User is not authenticated', content_type='text/plain', status=500)



@csrf_exempt
def gdal_ogrinfo(request):
    if request.user.is_authenticated:
        if settings.EMAIL_INSTANCE == "UAT" or settings.EMAIL_INSTANCE == "DEV":
            instance_format = settings.EMAIL_INSTANCE+'_'
        resp = sss_gdal.ogrinfo(request) 
        content_type='text/plain'
        output = ""
        if (isinstance(resp['output'], str)):
            return HttpResponse(resp['output'], content_type=content_type, status=500)
        if resp['format'] == 'json':
            content_type=resp['content_type']
            output = json.dumps(resp['output'])
        elif resp['format'] == 'plain':                           
            content_type=resp['content_type']
            output = resp['output']
            
        response = HttpResponse(output, content_type=content_type)    
        return response    
    else:
        return HttpResponse('User is not authenticated', content_type=content_type, status=500)
@csrf_exempt
def gdal_download(request, fmt):

    if request.user.is_authenticated:
        if settings.EMAIL_INSTANCE == "UAT" or settings.EMAIL_INSTANCE == "DEV":
            instance_format = settings.EMAIL_INSTANCE+'_'    
        resp = sss_gdal.download(request,fmt)
        output = resp['output']
        if resp['outputfile']:
            with open(pathlib.Path(resp['outputfile']), 'rb') as f:
                output = f.read()
        else:
            return HttpResponse(output, content_type='text/plain', status=500)
        response = HttpResponse(output, content_type=resp['filemime'])  
        response["Content-Disposition"] = "attachment;filename='{}'".format(resp["outputfilename"])
        return response    
    else:
        return HttpResponse('User is not authenticated', content_type='text/plain', status=500)    
    
def himawari8(request, target):
    last_updatetime = request.GET.get('updatetime')
    request_url = request.build_absolute_uri()
    baseUrl = request_url[0:request_url.find("/hi8")]
    key = "himawari8.{}".format(target)
    result = None
    getcaps = None
    FIREWATCH_HTTPS_VERIFY = True
    try:
        proxy = proxy_object("firewatch")
    except Proxy.DoesNotExist:
        raise Http404("No active Proxy entry found for firewatch")
    firewatch_caps_url = proxy["proxy_url"].rstrip("/") + "/wxs/westernpower-himawari8.php?service=wms&request=getcapabilities"
    auth = None
    if proxy["basic_auth_enabled"]:
        auth = HTTPBasicAuth(proxy["username"], proxy["password"])

    if cache.get("himware18") is not None:
        if cache.get(key) is not None:
            result = json.loads(cache.get(key))
        else:
            getcaps = cache.get("himware18")
    else:
        resp = requests.get(firewatch_caps_url, auth=auth, verify=FIREWATCH_HTTPS_VERIFY)
        resp.raise_for_status()
        getcaps = resp.content
        getcaps = getcaps.decode("utf-8")
        cache.set("himawari8", getcaps, 60 * 10)  # cache for 10 mins

    if not result:
    #     # Oct-2023: Himarwari layer names updated from *_HI8_* to *_HI9_*
        layernames = re.findall("\w+HI9\w+{}\.\w+".format(target), getcaps)
        layers = []

        for layer in layernames:
            layers.append([settings.PERTH_TIMEZONE.localize(datetime.datetime.strptime(re.findall("\w+_(\d+)_\w+", layer)[0], "%Y%m%d%H%M")), layer])

        layers = sorted(layers,key=lambda layer:layer[0])
        for layer in layers:
            layer[0] = (layer[0]).strftime("%a %b %d %Y %H:%M:%S AWST")

        result = {
            "servers": [baseUrl + conf.settings.FIREWATCH_SERVICE],
            "layers": layers,
            # "updatetime":layers[len(layers) - 1][0]
        }
        if len(layers) > 0:
            result["updatetime"] = layers[len(layers) - 1][0]
        else:
            result["updatetime"] = None

        cache.set(key, json.dumps(result), 60*10)  # cache for 10 mins
    if len(result["layers"]) == 0:
        return HttpResponse(status=404)
    elif last_updatetime and last_updatetime == result["updatetime"]:
        return JsonResponse({}, status=200)
    else:
        content_type = 'application/json'
        json_data = json.dumps(result)
        response = HttpResponse(json_data, content_type=content_type)
        return response
   
@csrf_exempt
def weatherforecast(request):
    try:
        if settings.WEATHERFORECAST_URL:
            if request.method == 'POST':
                requestData = request.POST.get("data")
                if requestData:
                    requestData = json.loads(requestData)
                else:
                    return JsonResponse({"error": "Request data is missing"}, status=400)

                requestData["weatherforecast_url"] = settings.WEATHERFORECAST_URL
                requestData["weatherforecast_user"] = settings.WEATHERFORECAST_USER
                requestData["weatherforecast_password"] = settings.WEATHERFORECAST_PASSWORD

                template_dir = os.path.join(settings.JINJA2_BASE_TEMPLATE, 'weather')
                jinja_env = Environment(loader=FileSystemLoader(template_dir))
                
                template = jinja_env.get_template('weatherforecast.html')

                rendered_template = template.render(
                    envType=settings.ENV_TYPE,
                    request_time=datetime.datetime.now(settings.PERTH_TIMEZONE),
                    **requestData
                )
                return HttpResponse(rendered_template)

            else:
                return JsonResponse({"error": "Invalid request method"}, status=405)
        else:
            return HttpResponse("Path '/weatherforecast' Not Found", content_type="text/plain", status=404)

    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({"error": "An error occurred"}, status=500)

@csrf_exempt    
def bfrs_calculation_queue(request):
    if request.user.is_authenticated:
        bfrs = request.POST.get('bfrs')
        features = request.POST.get("features")
        options = request.POST.get("options")
        user_email = request.user.email
        tasks = request.POST.get("tasks")
        user = request.user
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = "Added by {} on {}".format(user_email, current_time)
        caculation_queue_object = SpatialDataCalculation.objects.create(bfrs=bfrs, features=features, tasks=tasks, options=options, calculation_status=SpatialDataCalculation.CALCULATION_STATUS[0][0], user=user, logs=log_entry)
        content_type = 'application/json'
        data = {"bfrs": bfrs, "calculation_status": caculation_queue_object.calculation_status}
        response = HttpResponse(json.dumps(data), content_type=content_type)    
        return response    
    else:
        return HttpResponse('User is not authenticated', content_type='text/plain', status=500)

@csrf_exempt
def spatial_calculation_progress(request, *args, **kwargs):
    if request.user.is_authenticated:
        bfrs = request.POST.get('bfrs')
        tasks = request.POST.get('tasks')
        spatial_data = request.POST.get('spatial_data')
        if 'new bushfire' in bfrs.lower():
            # only fetch the bushfire uploaded by the user in case of new bushfire
            calculation_object = SpatialDataCalculation.objects.filter(bfrs=bfrs, user=request.user).last()
        else:
            calculation_object = SpatialDataCalculation.objects.filter(bfrs=bfrs).last()
        calculation_object.tasks = tasks
        if (spatial_data != "" and spatial_data != "null"):
            calculation_object.spatial_data = spatial_data
        calculation_object.save()
        last_uploaded_date = calculation_object.created.astimezone(conf.settings.PERTH_TIMEZONE).strftime('%a %b %d %Y %H:%M:%S AWST')
        submitter = calculation_object.user.email
        if(calculation_object.output):
            # calculation_object.output is stored as the Python repr() of a dict, which
            # uses single-quoted strings (e.g. {'key': 'value'}).
            #
            # The previous approach of .replace("'", '"') was fragile:
            #   - It broke whenever a string value contained an apostrophe
            #     (e.g. layer names like 'cddp:legislated_lands_and_waters').
            #   - Its companion .replace("nan", "null") had no word-boundary guard,
            #     so it would corrupt any value containing "nan" as a substring
            #     (e.g. a hypothetical property value "banana" would become "baNulla").
            #
            # ast.literal_eval() correctly parses Python literal syntax, including
            # nested dicts/lists and single-quoted strings with apostrophes.
            #
            # One pre-processing step is required: bare `nan` tokens produced by
            # float('nan') area calculations are not valid Python literals, so they
            # are replaced with None via a word-boundary regex before parsing.
            # The \bnan\b pattern avoids corrupting substrings like "banana".
            # Note: if a string *value* happened to be exactly "nan" (very unlikely
            # for WA spatial data), it would become the string "None" instead — an
            # acceptable trade-off vs. the original approach which was more broken.
            #
            # Finally, json.dumps/loads round-trips the result to ensure the
            # structure is fully JSON-serialisable (e.g. Python None → JSON null).
            raw = ast.literal_eval(re.sub(r'\bnan\b', 'None', calculation_object.output))
            result = json.loads(json.dumps(raw))
        else:
            result = ""
        output = {"status": calculation_object.calculation_status, "result": result, "last_uploaded_date":last_uploaded_date, "submitter":submitter, "feature": calculation_object.features, "spatial_data": calculation_object.spatial_data }
        
        if(calculation_object.calculation_status == SpatialDataCalculation.CALCULATION_STATUS[3][0]):
            output["error"] = calculation_object.error
        
        output = json.dumps(output)
        return HttpResponse(output, content_type='application/json')
    else:
        raise ValidationError('User is not authenticated') 

def update_tasks(request, *args, **kwargs):
    if request.user.is_authenticated:
        bfrs = request.GET.get('bfrs')
        tasks = request.GET.get('tasks')
        tasks_list = json.loads(tasks)
        if 'new bushfire' in bfrs.lower():
            # only update the bushfire uploaded by the user in case of new bushfire
            calculation_object = SpatialDataCalculation.objects.filter(bfrs=bfrs, user=request.user).last()
        else:
            calculation_object = SpatialDataCalculation.objects.filter(bfrs=bfrs).last()
        if tasks_list:
            calculation_object.tasks = tasks
            calculation_object.save()
        
        return JsonResponse({"tasks":"updated"})
    else:
        raise ValidationError('User is not authenticated') 



@csrf_exempt
def load_bfrs_status(request, *args, **kwargs):
    if request.user.is_authenticated:
        # Get the latest entry for each unique bfrs
        latest_entries = SpatialDataCalculation.objects.all().values('bfrs').annotate(latest_id=Max('id'))
        latest_ids = [entry['latest_id'] for entry in latest_entries]

        # Common status filter
        status_filter = (
            Q(calculation_status=SpatialDataCalculation.CALCULATION_STATUS[0][0]) | 
            Q(calculation_status=SpatialDataCalculation.CALCULATION_STATUS[1][0]) |
            Q(calculation_status=SpatialDataCalculation.CALCULATION_STATUS[2][0]) |
            Q(calculation_status=SpatialDataCalculation.CALCULATION_STATUS[3][0])
        )

        # Filter the main queryset
        bfrs_in_queue = SpatialDataCalculation.objects.filter(
            Q(id__in=latest_ids) & status_filter
        ).exclude(bfrs__icontains="new bushfire")

        # Filter 'New Bushfire' entries for the current user in the last 24 hours with same status conditions
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        new_bushfires = SpatialDataCalculation.objects.filter(
            bfrs__istartswith="New Bushfire",
            user=request.user,
            created__gte=twenty_four_hours_ago
        ).filter(status_filter)

        # Combine both querysets
        combined_queryset = list(bfrs_in_queue) + list(new_bushfires)

        bfrs_list = [
            {
                'bfrs': obj.bfrs,
                'feature': obj.features,
                'tasks': obj.tasks,
                'spatial_data': obj.spatial_data
            }
            for obj in combined_queryset
        ]

        return JsonResponse({'bfrs_list': bfrs_list})
    else:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

@csrf_exempt
def clear_queue(request, *args, **kwargs):
    if request.user.is_authenticated:
        bfrs = request.POST.get('bfrs')
        status = request.POST.get('status')
        removed = request.POST.get('removed')
        if 'new bushfire' in bfrs.lower():
            # only delete the bushfire uploaded by the user in case of new bushfire
            bfrs_in_queue = SpatialDataCalculation.objects.filter(bfrs=bfrs, user=request.user).last()
        else:
            bfrs_in_queue = SpatialDataCalculation.objects.filter(
                bfrs = bfrs
            ).last()
        if 'error' in status.lower():
            bfrs_in_queue.calculation_status = SpatialDataCalculation.CALCULATION_STATUS[5][0]
        else:
            bfrs_in_queue.calculation_status = SpatialDataCalculation.CALCULATION_STATUS[4][0]
        user = request.user.email
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if removed == 'true':
            log_entry = "Removed by {} on {}".format(user, current_time)
        else:
            log_entry = "Completed by {} on {}".format(user, current_time)
        if bfrs_in_queue.logs is None:
            bfrs_in_queue.logs = ''
        bfrs_in_queue.logs += f"\n{log_entry}"
        bfrs_in_queue.save()
        return JsonResponse({'bfrs': bfrs})
    else:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

@csrf_exempt
def command_status(request, *args, **kwargs):
    if request.user.is_authenticated is False:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
    # Get all successfully completed command statuses
    completed_commands = ManagementCommandStatus.objects.filter(
        completion_time__isnull=False
    )
    sss_data = {}
    now = timezone.now()

    for command_status in completed_commands:
        time_difference = now - command_status.completion_time
        seconds_ago = int(time_difference.total_seconds())
        sss_data[command_status.command] = seconds_ago
        
    response_data = {
        'sss': sss_data
    }
    
    return JsonResponse(response_data)

@csrf_exempt
def api_bfrs_proxy(request, *args, **kwargs):
    if not request.user.is_authenticated:
        raise ValidationError('User is not authenticated')

    base_url = getattr(settings, "BFRS_PROXY_URL", None)
    if not base_url:
        return JsonResponse({"error": "BFRS_PROXY_URL not configured"}, status=500)

    remoteurl = base_url + "/api/bushfirelist_latest/"
    query_string = request.META.get("QUERY_STRING", "")

    target_url = remoteurl
    if query_string:
        target_url = f"{remoteurl}?{query_string}"

    auth_request = HTTPBasicAuth(
        settings.AUTH2_BASIC_AUTH_USER,
        settings.AUTH2_BASIC_AUTH_PASSWORD
    )

    try:
        response = requests.get(
            target_url,
            auth=auth_request
        )

        return HttpResponse(
            response.content,
            content_type=response.headers.get("Content-Type", "application/json"),
            status=response.status_code
        )

    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)