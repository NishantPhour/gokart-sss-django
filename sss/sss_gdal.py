import sys
import os
import shutil
import subprocess
import tempfile
import requests
import datetime
import re
import json
import traceback
from jinja2 import Template
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from sss import s3
from sss import common
from sss import kmi
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import File
import http
import base64
import hashlib
from django.http import HttpResponse
import time

gdalinfo = subprocess.check_output(["gdalinfo", "--version"])

def convert_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode('utf-8')
    return encoded_string


import requests
from requests.auth import HTTPBasicAuth

def get_chunks(base_str, chunk_size):
    count = 0
    chunks = []
    
    for i in range(0, len(base_str), chunk_size):
        count += 1
        chunk = base_str[i:i + chunk_size]
        chunks.append({
            'part': count,
            'data': chunk
        })
    
    return chunks

def send_file(base64_encoded_file, hash_key, fmt, request):
    url = f"{settings.SSS_FILE_URL}/api/store_map_pdf/"
    auth_request = HTTPBasicAuth(settings.AUTH2_SSS_MAP_USER, settings.AUTH2_SSS_MAP_PASSWORD)
    
    # Chunk the base64-encoded file
    chunk_size = 200000 #200KB each chunk size
    chunks = get_chunks(base64_encoded_file, chunk_size)
    total_parts = len(chunks)
    
    # Send each chunk as a separate request
    for chunk in chunks:
        data = {
            'base64_file': chunk['data'],
            'hash': hash_key,
            'extension': fmt,
            'part_number': chunk['part'],
            'total_parts': total_parts
        }
        response = requests.post(url, data=data, auth=auth_request)
        
        if response.status_code not in [200,201]:
            print(f"Error: {response.status_code}")
            break
    
    return response


# PDF renderer, accepts a JPG
def gdal_convert(request, fmt):
    # needs gdal 1.10+

    instance_format = ""
    if settings.EMAIL_INSTANCE == "UAT" or settings.EMAIL_INSTANCE == "DEV":
        instance_format = settings.EMAIL_INSTANCE+'_'

    extent = request.POST.get("extent").split(" ")
    hash_key = request.POST.get("hash_key")
    jpg = request.FILES.get("jpg")
    title = request.POST.get("title") or "Quick Print"
    sso_user = request.headers.get("X-email", "unknown")
    workdir = tempfile.mkdtemp()    
    path = os.path.join(workdir, instance_format+'_'+jpg.name)
    output_filepath = path + "." + fmt
    
    #--    
    fout = open(path, 'wb+')
    file_content = ContentFile( jpg.read() )

    # Iterate through the chunks.
    for chunk in file_content.chunks():
        fout.write(chunk)
    fout.close()


    # copy input and output file to temp disk storage
    disk_temp_dir = "/" + settings.TEMP_DIR + "/temp_storage"
    os.makedirs(disk_temp_dir, exist_ok=True)

    input_temp_path = os.path.join(disk_temp_dir, os.path.basename(path))
    shutil.copy2(path, input_temp_path)

    output_temp_path = os.path.join(disk_temp_dir, os.path.basename(output_filepath))

    path = input_temp_path
    output_filepath = output_temp_path

    #---
    #shutil.copy(jpg.name, workdir)
    #jpg.save(workdir)
    legends_path = None
    
    extra = []
    if fmt == "tif":
        of = "GTiff"
        ct = "image/tiff"
        extra = ["-co", "COMPRESS=JPEG", "-co", "PHOTOMETRIC=YCBCR", "-co", "JPEG_QUALITY=95"]
    elif fmt == "pdf":
        of = "PDF"
        ct = "application/pdf"
        legends = request.FILES.get("legends")
        if legends:
            legends_path = os.path.join(workdir, legends.name)
            #legends.save(workdir)

            fout = open(legends_path, 'wb+')
            file_content = ContentFile( legends.read() )        
            # Iterate through the chunks.
            for chunk in file_content.chunks():
                fout.write(chunk)
            fout.close()
            
            # copy legend file to temp disk storage
            legend_temp_path = os.path.join(disk_temp_dir, os.path.basename(legends_path))
            shutil.copy2(legends_path, legend_temp_path)
            legends_path = legend_temp_path

            
    else:
        raise Exception("File format({}) Not Support".format(fmt))

    subprocess.check_call([
        "gdal_translate", "-of", of, "-a_ullr", extent[0], extent[3], extent[2], extent[1],
        "-a_srs", "EPSG:4326", "-co", "DPI={}".format(request.POST.get("dpi", 150)),
        "-co", "TITLE={}".format(title),
        "-co", "AUTHOR={}".format("Department of Parks and Wildlife"),
        "-co", "PRODUCER={}".format(gdalinfo),
        "-co", "SUBJECT={}".format(request.headers.get('Referer', "gokart")),
        "-co", "CREATION_DATE={}".format(datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y%m%d%H%M%SZ'00'"))] + extra + [
        path, output_filepath
    ])
    output_filename = instance_format+jpg.name.replace("jpg", fmt)

    #merge map pdf and legend pdf
    if fmt == "pdf" and legends_path:
        #dump meta data
        metadata_file = output_filepath + ".txt"
        subprocess.check_call(["pdftk",output_filepath,"dump_data_utf8","output",metadata_file])
        #merge two pdfs
        merged_filepath = ".merged".join(os.path.splitext(output_filepath))
        subprocess.check_call(["pdftk",output_filepath,legends_path,"output",merged_filepath])
        #update meta data
        updated_filepath = ".updated".join(os.path.splitext(output_filepath))
        subprocess.check_call(["pdftk",merged_filepath,"update_info_utf8",metadata_file,"output",updated_filepath])
        output_filepath = updated_filepath

    base64_encoded_file = convert_file_to_base64(output_filepath)
    
    # store the map pdf in sss-maps
    response = send_file(base64_encoded_file, hash_key, fmt, request)
    if response.status_code != 201:
        try:
            error_message = response.json().get('message', 'Error storing the file in server')
        except ValueError:
            error_message = response.text 
        raise Exception(error_message)
    with open(output_filepath, 'rb') as f:
        output = f.read()
    shutil.rmtree(os.path.dirname(output_filepath))

    response = HttpResponse(output, content_type=ct)
    response["Content-Disposition"] = "attachment; filename='{}'".format(output_filename)
    return response
    
    # meta = {
    #     'SSOUser': sso_user
    # }

    # #upload to s3
    # if hash_key:
    #     #only upload to s3 if bucket_key is not empty
    #     s3.upload_map(hash_key, output_filepath, output_filename, ct, meta)
    # #output = open(output_filepath)
    # output = ""       
    # with open(output_filepath, 'rb') as f:
    #     output = f.read()
    # shutil.rmtree(workdir)
    # #bottle.response.set_header("Content-Type", ct)
    # #bottle.response.set_header("Content-Disposition", "attachment;filename='{}'".format(output_filename))
    # return output

def detectEpsg(filename):

    gdal_cmd = ['gdalsrsinfo', '-e', filename]
    gdal = subprocess.Popen(gdal_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gdal_output = gdal.communicate()
    result = None
    print (gdal_output[0].decode())
    for line in gdal_output[0].decode().split('\n'):
        if line.startswith('EPSG') and line != 'EPSG:-1':
            result = line
            break

    return result

def validateCRS(filename):
    gdal_cmd = ['gdalsrsinfo', '-o', 'wkt2', filename]
    gdal = subprocess.Popen(gdal_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gdal_output = gdal.communicate()
    proj4_string = gdal_output[0].decode().split('\n')

    for line in proj4_string:
        if line.startswith("PROJCRS") or line.startswith("GEOGCRS"):
            for crs_name in line.split('"'):
                if crs_name.lower() in [supported_crs.lower() for supported_crs in SUPPORTED_CRS.keys()]:
                    return crs_name
            return False
    return True



#initialize vrt template
with open(os.path.join(settings.BASE_PATH,"sss","unionlayers.vrt")) as f:
    UNIONLAYERS_TEMPLATE = Template(f.read())

# Vector translation using ogr
SUPPORTED_GEOMETRY_TYPES = ["POINT","LINESTRING","POLYGON","MULTIPOINT","MULTILINESTRING","MULTIPOLYGON"] 

SUPPORTED_CRS = {
    "Albers_Equal_Conic_Area_GDA_Western_Australia": "aea", #no EPSG code for this projection
    "Albers Equal Area Conic Western Australia GDA2020": "aea", #no EPSG code for this projection
    "GDA2020": "EPSG:7844",
    "GCS_GDA2020": "EPSG:7844",   # ESRI legacy .prj naming convention
    "GDA2020_3D": "EPSG:7844",
    "GDA94": "EPSG:4283",
    "GCS_GDA_1994": "EPSG:4283",  # ESRI legacy .prj naming convention
    "GDA94 / MGA zone 49": "EPSG:28349",
    "GDA94 / MGA zone 50": "EPSG:28350",
    "GDA94 / MGA zone 51": "EPSG:28351",
    "GDA94 / MGA zone 52": "EPSG:28352",
    "GDA2020 / MGA zone 49": "EPSG:7849",
    "GDA2020 / MGA zone 50": "EPSG:7850",
    "GDA2020 / MGA zone 51": "EPSG:7851",
    "GDA2020 / MGA zone 52": "EPSG:7852",
    "WGS 84": "EPSG:4326",
    "GDA94 / Australian Albers": "EPSG:3577",
    "GDA2020 / Australian Albers": "EPSG:9473"
}

#initialize supported spatial format
SPATIAL_FORMAT_LIST = [
    {
        "name"      : "shp",
        "format"    : "ESRI Shapefile",
        "multilayer": False,
        "multitype" : False,
        "fileext"   : ".shp"
    },
    {
        "name"      : "sqlite",
        "format"    : "SQLite",
        "mime"      : "application/x-sqlite3",
        "multilayer": True,
        "multitype" : False,
        "fileext"   : ".sqlite"
    },
    {
        "name"      : "gpkg",
        "format"    : "GPKG",
        "mime"      : "application/x-sqlite3",
        "multilayer": True,
        "multitype" : False,
        "fileext"   : ".gpkg",
    },
    {
        "name"      : "csv",
        "format"    : "CSV",
        "mime"      : "text/csv",
        "multilayer": False,
        "multitype" : True,
        "fileext"   : ".csv"
    },
    {
        "name"      : "geojson",
        "format"    : "GeoJSON",
        "mime"      : "application/vnd.geo+json",
        "multilayer": False,
        "multitype" : True,
        "fileext"   : ".geojson",
        "ogr2ogr_arguments":["-mapFieldType","DateTime=String"],
    },
    {
        "name"      : "json",
        "format"    : "GeoJSON",
        "mime"      : "application/vnd.geo+json",
        "multilayer": False,
        "multitype" : True,
        "fileext"   : ".json",
        "ogr2ogr_arguments":["-mapFieldType","DateTime=String"],
    },
    {
        "name"      : "gpx",
        "format"    : "GPX",
        "mime"      : "application/gpx+xml",
        "multilayer": True,
        "multitype" : False,
        "fileext"   : ".gpx"
    }
]
SPATIAL_FORMATS = {}
for f in SPATIAL_FORMAT_LIST:
    SPATIAL_FORMATS[f["name"]] = f
    SPATIAL_FORMATS[f["fileext"]] = f

#initialize supported compressed file format
COMPRESS_FILE_SETTINGS = {
    ".7z":lambda f,output:["7za","x",f,"-o{}".format(output)],
    ".zip":lambda f,output:["unzip",f,"-d",output],
    ".tar":lambda f,output:["tar","-x","-f",f,"-C",output],
    ".tar.gz":lambda f,output:["tar","-x","-z","-f",f,"-C",output],
    ".tgz":lambda f,output:["tar","-x","-z","-f",f,"-C",output],
    ".tar.xz":lambda f,output:["tar","-x","-J","-f",f,"-C",output],
    ".tar.bz2":lambda f,output:["tar","-x","-j","-f",f,"-C",output],
    ".tar.bz":lambda f,output:["tar","-x","-j","-f",f,"-C",output],
}
def getBaseDatafileName(f,includeDir=False):
    if not includeDir:
        f = os.path.split(f)[1]
    for fileext in COMPRESS_FILE_SETTINGS.keys():
        if f.lower().endswith(fileext):
            return f[0:len(f) - len(fileext)]

    for fmt in SPATIAL_FORMAT_LIST:
        if f.lower().endswith(fmt["fileext"]):
            return f[0:len(f) - len(fmt["fileext"])]

    return os.path.splitext(f)[0]

#return list of spatial data files. each data file has absolute path and relative path
def getDatasourceFiles(workdir,datasourcefile):
    # needs gdal 1.10+
    datasourcefiles = []
    #import ipdb;ipdb.set_trace()
    #uncompress files, support recursive uncompress
    files = [datasourcefile]

    while len(files) > 0:
        f = files.pop()

        if os.path.isfile(f):

            for (fileext,cmd) in COMPRESS_FILE_SETTINGS.items():
  
                if f.lower().endswith(fileext):

                    extractDir = f[0:len(f) - len(fileext)]
                    os.mkdir(extractDir)
                    subprocess.check_call(cmd(f,extractDir))

                    if f != datasourcefile:
                        os.remove(f)
                    else:
                        datasourcefile = extractDir

                    files.append(extractDir)

                    break
        else:

            files.extend([os.path.join(f,path) for path in os.listdir(f)])

    if os.path.isdir(datasourcefile):
        for f in os.walk(datasourcefile):
            for fileName in f[2]:
                if (fileName[0] == "."):
                    #ignore the file starts with "."
                    continue
                else:
                    if os.path.splitext(fileName)[1] in SPATIAL_FORMATS:
                        datasourcefiles.append((os.path.join(f[0],fileName),os.path.relpath(os.path.join(f[0],fileName),datasourcefile)))
    
    elif os.path.splitext(datasourcefile)[1] in SPATIAL_FORMATS:
        datasourcefiles = [(datasourcefile,os.path.relpath(datasourcefile,workdir))]

    return datasourcefiles

layer_re = re.compile("[\r\n]+Layer name:")
layer_info_re = re.compile("[\r\n]+(?P<key>[a-zA-Z0-9_\-][a-zA-Z0-9_\- ]*)[ \t]*[:=](?P<value>[^\r\n]*([\r\n]+(([ \t]+[^\r\n]*)|(GEOGCS[^\r\n]*)))*)")
extent_re = re.compile("\s*\(\s*(?P<minx>-?[0-9\.]+)\s*\,\s*(?P<miny>-?[0-9\.]+)\s*\)\s*\-\s*\(\s*(?P<maxx>-?[0-9\.]+)\s*\,\s*(?P<maxy>-?[0-9\.]+)\s*\)\s*")
field_re = re.compile("[ \t]*(?P<type>[a-zA-Z0-9]+)[ \t]*(\([ \t]*(?P<width>[0-9]+)\.(?P<precision>[0-9]+)\))?[ \t]*")
def getLayers(datasource,layer=None,srs=None,defaultSrs=None,featureType=None):
    # needs gdal 1.10+
    infoIter = None

    srs = srs or detectEpsg(datasource) or defaultSrs
    x = validateCRS(datasource)

    #import ipdb;ipdb.set_trace()
    cmd = ["ogrinfo", "-al","-so","-ro"]
    if featureType:
        if featureType == "EMPTY":
            cmd.extend(["-where", "OGR_GEOMETRY IS NULL"])
        else:
            cmd.extend(["-where", "OGR_GEOMETRY='{}'".format(featureType)])

    cmd.append(datasource)

    if layer:
        cmd.append(layer)

    def getLayerInfo(layerInfo):
        info = {"fields":[],"srs":srs}
        for m in layer_info_re.finditer(layerInfo):
            key = m.group("key")
            lkey = key.lower()
            value = m.group("value").strip()
            if lkey in ("info","metadata","layer srs wkt","ogrinfo"): 
                continue
            if lkey == "layer name":
                info["layer"] = value
            elif lkey == "geometry":
                info["geometry"] = value.replace(" ","").upper()
            elif lkey == "feature count":
                try:
                    info["features"] = int(value)
                except:
                    info["features"] = 0
            elif lkey == "extent":
                try:
                    info["extent"] = [float(v) for v in extent_re.search(value).groups()]
                except:
                    pass
            elif lkey == "fid column":
                info["fid_column"] = value
            elif lkey == "geometry column":
                info["geometry_column"] = value
            else:
                m = field_re.search(value)
                info["fields"].append([lkey,m.group('type'),m.group('width'),m.group('precision')])

        return info

    info_encoded = subprocess.check_output(cmd)
    info = info_encoded.decode()
    layers = []
    previousMatch = None

    layerIter = layer_re.finditer(info)
    for m in layerIter:
        if previousMatch is None:
            previousMatch = m
        else:
            layers.append(getLayerInfo(info[previousMatch.start():m.start()]))
            previousMatch = m
    if previousMatch:
        layers.append(getLayerInfo(info[previousMatch.start():]))

    return layers

def getFeatureCount(datasource,layer=None,featureType=None):
    layers = getLayers(datasource,layer,None,None,featureType)
    if len(layers) == 0:
        raise Exception("Layer({}) is not found in datasource({})".format(layer or "",datasource))
    elif len(layers) > 1:
        raise Exception("Multiple layers are found in datasource({})".format(datasource))
    else:
        return layers[0].get("features") or 0

def getOutputDatasource(workdir,fmt,layer,geometryType=None):
    if geometryType:
        geometryType = layer.get("type_mapping",{}).get(geometryType,geometryType)
    if fmt["multilayer"]:
        if geometryType:
            path = os.path.join(workdir,"{}-{}{}".format(layer["sourcename"],geometryType,fmt["fileext"]))
        else:
            path = os.path.join(workdir,"{}{}".format(layer["sourcename"],fmt["fileext"]))
    elif layer.get("sourcename",None):
        if geometryType:
            path = os.path.join(workdir,layer["sourcename"],"{}-{}{}".format(layer["layer"],geometryType,fmt["fileext"]))
        else:
            path = os.path.join(workdir,layer["sourcename"],"{}{}".format(layer["layer"],fmt["fileext"]))
    else:
        if geometryType:
            path = os.path.join(workdir,"{}-{}{}".format(layer["layer"],geometryType,fmt["fileext"]))
        else:
            path = os.path.join(workdir,"{}{}".format(layer["layer"],fmt["fileext"]))
    
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path

geojson_re = re.compile("^\s*\{\s*[\"\']type[\"\']\s*:\s*[\"\']FeatureCollection[\"\']\s*\,")
service_exception_re = re.compile("^.*(\<ServiceExceptionReport)",re.DOTALL)
def loadDatasource(session_cookie,workdir,loadedDatasources,options, request):
    """
    options:{
        name: datasource name, optional; if missing, derived from url or parameter
        type: "WFS" or "UPLOAD" or "FORM"  
            WFS: download the data from wfs server; 
            UPLOAD: download the data from http request
            FORM: get the data form http form
        url: wfs url if sourcetype is "WFS",
        parameter: http request parameter if sourcetype is"UPLOAD" or "FORM"
        srs: srs optional
        datasource: used if sourcetype is "UPLOAD" and uploaded file contains multiple datasources
        layer: layer name,required if datasource include multiple layers
        where: filter the features 
    }
    After loading, the following data are inserted into options
        name: add if missing
        file: the loaded file
        datasources: datasource list included in the datasource
        datasource: the datasource selected by user
        srs: if can be determined
        format: the source data file format, optional, can be deduced from datasource
        layer: layer name,required if datasource include multiple layers
        meta: the layer information: geometry type, feature count, etc, optional. can be deduced from datasource and name
    """
    #import ipdb;ipdb.set_trace()
    sourcetype = options.get("type","WFS")
    if sourcetype == "WFS":
        #load layer from wfs server
        if options["url"] not in loadedDatasources:
            datasource = os.path.join(workdir,"{}.geojson".format(options["sourcename"]))
            if not os.path.exists(os.path.dirname(datasource)):
                os.makedirs(os.path.dirname(datasource))
            url = "{}&outputFormat=application%2Fjson&srsName=EPSG:4326".format(options["url"])
            parsed_url = urlsplit(url)
            query = {key.lower(): value for key, value in parse_qs(parsed_url.query).items()}
            layerid = (query.get("typenames") or query.get("typename") or [""])[0].split(",")[0]
            if kmi.is_kb_layer(layerid):
                url = kmi.get_kmiserver(layerid=layerid) + "/geoserver/wfs?" + parsed_url.query
            auth_request = kmi.get_auth(layerid)
            r = requests.get(url,
                verify=kmi.is_kb_layer(layerid),
                #cookies=session_cookie
                auth=auth_request
            )
            r.raise_for_status()
            with open(datasource,"wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            failed = False
            with open(datasource,"r") as f:
                if service_exception_re.search(f.read(1024)):
                    failed = True
            if failed:
                with open(datasource,"r") as f:
                    raise Exception("{}\r\n{}".format(url,f.read()))

            loadedDatasources[options["url"]] = (datasource,getDatasourceFiles(os.path.dirname(datasource),datasource))
        options["srs"] = "EPSG:4326"
        options["file"] = loadedDatasources[options["url"]][0]
        options["datasources"] = loadedDatasources[options["url"]][1]

    elif sourcetype in ["UPLOAD","FORM"]:
        if options["parameter"] not in loadedDatasources:
            if sourcetype == "UPLOAD":
                #load layer from http request
                datasource = request.FILES.get(options["parameter"])
                #datasource.save(workdir,overwrite=True)
                datasource_path =  os.path.join(workdir,datasource.name)

                fout = open(datasource_path, 'wb+')
                file_content = ContentFile( datasource.read() )        
                # Iterate through the chunks.
                for chunk in file_content.chunks():
                    fout.write(chunk)
                fout.close()

                loadedDatasources[options["parameter"]] = (datasource_path,getDatasourceFiles(os.path.dirname(datasource_path),datasource_path))
    
            elif sourcetype == "FORM":
                #load layer from http request
                datasource = os.path.join(workdir,"{}.geojson".format(options.get("parameter")))
                if not os.path.exists(os.path.dirname(datasource)):
                    os.makedirs(os.path.dirname(datasource))
                with open(datasource,"wb") as f:
                    f.write(bytes(request.POST.get(options["parameter"]),'utf-8'))
                    
                loadedDatasources[options["parameter"]] = (datasource,getDatasourceFiles(os.path.dirname(datasource),datasource))
    
        options["file"] = loadedDatasources[options["parameter"]][0]
        options["datasources"] = loadedDatasources[options["parameter"]][1]

    if len(options["datasources"]) == 0:
        raise Exception("No spatial data are found in datasource  ({}).".format(options["sourcename"]))

    #get the datasource selected by user
    if options.get("datasource"):
        if options["datasource"] == "*":
            #include all datasource and layers; used when loading a datasource
            return
        else:
            #have selected datasource , find it
            datasource = None
            for d in options["datasources"]:
                if d[1] == options["datasource"]:
                    datasource = d
                    break

            if datasource:
                options["datasource"] = datasource
            else:
                raise Exception("Datasource({}) does not exist.".format(options["datasource"]))

    elif len(options["datasources"]) > 1:
        raise Exception("Multiple datasource({}) are found, please choose one".format(str([d[1] for d in options["datasources"]])))
    else:
        #only have one datasource,choose it
        options["datasource"] = options["datasources"][0]

    #detect srs
    if not options.get("srs"):
        options["srs"] = detectEpsg(options["datasource"][0])
        x = validateCRS(options["datasource"][0])
    if not options.get("srs") and options.get("default_srs"):
        options["srs"] = options["default_srs"]

    if "format" not in options:
        options["format"] = SPATIAL_FORMATS.get(os.path.splitext(options["datasource"][1])[1].lower())
        if not options["format"]:
            raise Exception("Can't detect the format of the datasource ({}).".format(options["datasource"][1]))

    #filter the data if required
    if "where"  in options:
        filterdir = os.path.join(workdir,"filter")
        if not os.path.exists(filterdir):
            os.mkdir(filterdir)
    
        datasource = os.path.join(filterdir,"{}{}".format(options["sourcename"],options["format"]["fileext"]))
        if not os.path.exists(os.path.dirname(datasource)):
            os.makedirs(os.path.dirname(datasource))
        
        cmd = ["ogr2ogr","-preserve_fid" ,"-skipfailures",
            #"-where","\"{}\"".format(options["where"]),
            "-where",options["where"],
            "-f", options["format"]["format"],
            datasource, 
            options["datasource"][0],
        ]
        
        if "layer" in options:
            cmd.append(options["layer"])

        #print " ".join(cmd)
        if "ogr2ogr_arguments" in options["format"]:
            index = 1
            for arg in options["format"]["ogr2ogr_arguments"]:
                cmd.insert(index,arg)
                index += 1
        subprocess.check_call(cmd)
        options["datasource"] = getDatasourceFiles(filterdir,datasource)[0]

        options["format"] = SPATIAL_FORMATS.get(os.path.splitext(options["datasource"][1])[1].lower())
        if not options["format"]:
            raise Exception("Can't detect the format of the datasource ({}).".format(options["datasource"][1]))

    #get layer meta data
    if "format" not in options:
        options["format"] = SPATIAL_FORMATS.get(os.path.splitext(options["datasource"][1])[1].lower())
        if not options["format"]:
            raise Exception("Can't detect the format of the datasource ({}).".format(options["datasource"][1]))

    if "meta" not in options:
        if options["format"]["multilayer"]:
            metas = getLayers(options["datasource"][0],options.get("layer"),options.get("srs"),options.get("default_srs"))
        else:
            metas = getLayers(options["datasource"][0],None,options.get("srs"),options.get("default_srs"))
        if len(metas) == 0:
            options["meta"] = None
            options["layer"] = None
        elif len(metas) == 1:
            options["meta"] = metas[0]
            options["layer"] = options["meta"]["layer"]
        else:
            raise Exception("Multiple layers are found in datasource({})".format(options["sourcename"]))
    
def ogrinfo(request):
    # needs gdal 1.10+
    #import ipdb;ipdb.set_trace()
    datasource = request.FILES.get("datasource")
    workdir = tempfile.mkdtemp()

    try:
        #datasource.save(workdir)
        datasourcefile = os.path.join(workdir, datasource.name)
        crs_validation = request.POST.get("crs_validation", False)
        print (datasourcefile)
        fout = open(datasourcefile, 'wb+')
        file_content = ContentFile( datasource.read() )

        # Iterate through the chunks.
        for chunk in file_content.chunks():
            fout.write(chunk)
        fout.close()

        datasources = []
        layerSize = 0
        datasourceSize = 0

        for filePath,relativeFilePath in getDatasourceFiles(workdir,datasourcefile):
            layers = getLayers(filePath)

            if crs_validation:
                crs = validateCRS(filePath)
                if crs == False:
                    raise Exception(f"Source CRS is not supported. Supported CRS: {SUPPORTED_CRS}")
                elif crs == True:
                    pass
                else:
                    for layer in layers: layer['crs'] = crs
            
            layers = [l for l in layers if l["geometry"] in SUPPORTED_GEOMETRY_TYPES or l["geometry"].upper().find("UNKNOWN") >= 0]

            if layers:
                datasources.append({"datasource":relativeFilePath,"layers": layers})
                layerSize += len(datasources[len(datasources) - 1]["layers"])
                datasourceSize += 1

        if layerSize == 0:
            raise Exception("No spatial data is found.")

        return {"output" : { "layerCount":layerSize,"datasourceCount":datasourceSize,"datasources":datasources}, "content_type": "application/json", "format": "json"}
    except Exception as ex:
        #bottle.response.status = 500
        #bottle.response.set_header("Content-Type", "text/plain")

        return  {"output" : str(ex), "content_type":"text/plain", "format": "json"}

    finally:
        try:
            pass
            #shutil.rmtree(workdir)
        except:
            pass


GEOMETRY_TYPE_MAP={
    "POINT":"wkbPoint",
    "LINESTRING":"wkbLineString",
    "POLYGON":"wkbPolygon",
    "MULTIPOINT":"wkbMultiPoint",
    "MULTILINESTRING":"wkbMultiLineString",
    "MULTIPOLYGON":"wkbMultiPolygon",
    "GEOMETRYCOLLECTION":"wkbGeometryCollection"
}

def download(request, fmt):
    """
    form data:
    layers: a layer or a list of layer
        {
            sourcename: output datasource name; if missing, derived from layer name or datasource
            layer: output layer name,if missing, using the datasource layer name
            default_geometry_type: The geometry type of the empty geometry 
            type_mapping: the mapping between geometry type and business name used in the datasource or layer name
            srs: srs optional, default is first's source layer's srs
            ignore_if_empty: empty layer will not be returned if true; default is false
            sourcelayers: a source layer or a list of source layers
            {
                type: "WFS" or "UPLOAD" or "FORM". deduced from other properties
                    WFS: download the data from wfs server; 
                    UPLOAD: download the data from http request
                    FORM: get the data form http form
                url: wfs url if sourcetype is "WFS",
                parameter: http request parameter if sourcetype is"UPLOAD" or "FORM"
                srs: srs optional
                defautl_srs:default srs; optional
                datasource: used if sourcetype is "UPLOAD" and uploaded file contains multiple datasources
                layer: layer name,required if datasource include multiple layers
                where: filter the features 
            },
            geometry_column: dictionary
                name: geometry column name
                type: geometry column type
            field_strategy: default is Intersection
            fields: optional
        },
    datasources:a datasource or a list of datasource
        {
            type: "WFS" or "UPLOAD" or "FORM", if missing, try to deduced from other data source properties.
                  WFS: download the data from wfs server; 
                  UPLOAD: download the data from http request
                  FORM: get the data form http form
            url: wfs url if sourcetype is "WFS",
            parameter: http request parameter if sourcetype is"UPLOAD" or "FORM"
            srs: srs optional
            default_geometry_type: The geometry type of the empty geometry 
            defautl_srs:default srs; optional
            datasource: used if sourcetype is "UPLOAD" and uploaded file contains multiple datasources
            ignore_if_empty: empty layer will not be returned if true; default is false
            field_strategy: default is Intersection
            fields: optional
        }
    
    filename:optional, used when multiple output datasources are downloaded
    srs: optional, output srs
    """
    # needs gdal 1.10+
    layers = request.POST.get("layers")
    output = request.POST.get("output")
    datasources = request.POST.get("datasources")
    filename = request.POST.get("filename")
    outputSrs = request.POST.get("srs")

    try:
        if layers:
            layers = json.loads(layers)

        if layers and not isinstance(layers,list):
            #convert  a layer to a list of layer
            layers = [layers]

        if datasources:
            datasources = json.loads(datasources)

        if datasources and not isinstance(datasources,list):
            #convert  a datasource to a list of datasource
            datasources = [datasources]

        if not layers and not datasources:
            raise Exception("Both layers parameter and datasources parameter are missing.")

        if layers is None:
            layers = []

        #if output format is not set, set to the default format "geojson"
        fmt = SPATIAL_FORMATS.get(fmt.lower())
        if not fmt:
            raise Exception("Unsupported spatial format({})".format(fmt))

        #If a source layer is not a union layer, changed it to a union layer which only have one sub layer
        if layers:
            for layer in layers:
                if layer.get("fields"): 
                    index = 0
                    while  index < len(layer["fields"]):
                        if isinstance(layer["fields"][index],str):
                            layer["fields"][index] = {"name":layer["fields"][index],"src":layer["fields"][index]}
                        index += 1

                if not layer.get("sourcelayers"):
                    raise Exception("Missing 'sourcelayers' in layer ({})".format(json.dumps(layer)))
                elif not isinstance(layer["sourcelayers"],list):
                    layer["sourcelayers"] = [layer["sourcelayers"]]

                for slayer in layer["sourcelayers"]:
                    if slayer.get("fields"): 
                        index = 0
                        while  index < len(slayer["fields"]):
                            if isinstance(slayer["fields"][index],str):
                                slayer["fields"][index] = {"name":slayer["fields"][index],"src":slayer["fields"][index]}
                            index += 1
                    elif layer.get("fields"):
                        slayer["fields"] = layer["fields"]


        #set field strategy and ignore_if_empty for layers
        if layers:
            for layer in layers:
                if not layer.get("field_strategy"):
                    layer["field_strategy"] = "Intersection"
                layer["ignore_if_empty"] = layer.get("ignore_if_empty") or False
                #if geometry column is a string, change it to a dict
                if layer.get("geometry_column") and isinstance(layer["geometry_column"],str):
                    layer["geometry_column"] = {name:layer["geometry_column"]}

                if layer.get("geometry_column",{}).get("type"):
                    if layer["geometry_column"]["type"].upper() in GEOMETRY_TYPE_MAP:
                        layer["geometry_column"]["type"] = GEOMETRY_TYPE_MAP[layer["geometry_column"]["type"].upper()]
                    else:
                        del layer["geometry_column"]["type"]

        #set datasource's ignore_if_empty
        if datasources:
            for datasource in datasources:
                datasource["ignore_if_empty"] = datasource.get("ignore_if_empty") or False
                if datasource.get("fields"):
                    while  index < len(datasource["fields"]):
                        if isinstance(datasource["fields"][index],str):
                            datasource["fields"][index] = {"name":datasource["fields"][index],"src":datasource["fields"][index]}
                        index += 1

                if not datasource.get("field_strategy"):
                    datasource["field_strategy"] = "Intersection"

    
        def setDatasourceType(ds):
            if "type" in ds:
                return
            if "url" in ds:
                ds["type"] = "WFS"
            elif "parameter" in ds:
              
                if request.POST.get(ds["parameter"]):
                    ds["type"] = "FORM"
                elif request.FILES.get(ds["parameter"]):
                    ds["type"] = "UPLOAD"
                else:
                    raise Exception("Can't locate the http request data ({})".format(ds["parameter"]))
            else:
                raise Exception("Can't deduce the type of the datasource ({})".format(json.dumps(ds)))

        def getDatasourceName(ds,unique=False):
            if "sourcename" in ds:
                name = ds["sourcename"]
                if unique and "where" in ds:
                    name = "{}-{}".format(name,common.get_md5(ds["where"]))
            elif ds["type"] == "WFS":
                name = common.typename(ds["url"])
                if not name:
                    name = common.get_md5(ds["url"])
                    if unique and "where" in ds:
                        name = "{}-{}".format(name,common.get_md5(ds["where"]))
                else:
                    name = name.replace(":","_")
                    if unique:
                        if "where" in ds:
                            name = "{}-{}-{}".format(name,common.get_md5(ds["url"]),common.get_md5(ds["where"]))
                        else:
                            name = "{}-{}".format(name,common.get_md5(ds["url"]))
            elif ds["type"] == "FORM":
                name = ds["parameter"]
                if unique and "where" in ds:
                    name = "{}-{}".format(name,common.get_md5(ds["where"]))
            elif ds["type"] == "UPLOAD":
                filename = request.FILES.get(ds["parameter"]).name
                filename = os.path.split(filename)[1]
                name = None
                for fileext in COMPRESS_FILE_SETTINGS.keys():
                    if filename.lower().endswith(fileext):
                        name = filename[:len(filename) - len(fileext)]
                        break
                if not name:
                    name = os.path.splitext(filename)[0]
                if unique and "where" in ds:
                    name = "{}-{}".format(name,common.get_md5(ds["where"]))


            return name

        #set datasource type if not set
        #import ipdb;ipdb.set_trace()
        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    setDatasourceType(sourcelayer)

        if datasources:
            for ds in datasources:
                setDatasourceType(ds)

        #set the datasource name for all source layers or source datasources, if not set.
        names = {}
        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    name = getDatasourceName(sourcelayer)
                    names[name] = names.get(name,0) + 1
                    sourcelayer["sourcename"] = name
        if datasources:
            for ds in datasources:
                name = getDatasourceName(ds)
                names[name] = names.get(name,0) + 1
                ds["sourcename"] = name

        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    if names.get(sourcelayer["sourcename"],1) > 1:
                        sourcelayer["sourcename"] = getDatasourceName(sourcelayer,True)
        if datasources:
            for ds in datasources:
                if names.get(ds["sourcename"],1) > 1:
                    ds["sourcename"] = getDatasourceName(ds,True)
        del names

        #import ipdb;ipdb.set_trace()
        #load data sources
        workdir = tempfile.mkdtemp()

        cookies = settings.SESSION_COOKIE_NAME

        loaddir = os.path.join(workdir,"load")
        os.makedirs(loaddir, exist_ok=True)

        loadedDatasources = {}
        if layers:
            for layer in layers:
                for sourcelayer in layer["sourcelayers"]:
                    loadDatasource(cookies,loaddir,loadedDatasources,sourcelayer, request)
        
        #import ipdb;ipdb.set_trace()
        #load data sources and add all layers in datasources to layers
        if datasources:
            for datasource in datasources:
                datasource["datasource"] = datasource.get("datasource") or "*"
                loadDatasource(cookies,loaddir,loadedDatasources,datasource,request)
                for dsfile in datasource["datasources"]:
                    if datasource.get("datasource") != "*" and datasource.get("datasource") != dsfile[0]:
                        continue
                    for metadata in getLayers(dsfile[0]):
                        sourcelayer = dict(datasource)
                        if "default_geometry_type" in sourcelayer:
                            del sourcelayer["default_geometry_type"]
                        sourcelayer["datasource"] = dsfile[1]
                        sourcelayer["meta"] = metadata
                        sourcelayer["layer"] = metadata["layer"]
                        loadDatasource(cookies,loaddir,loadedDatasources,sourcelayer,request)

                        layer = {
                            "sourcename":getBaseDatafileName(dsfile[1],True),
                            "sourcelayers":[sourcelayer],
                            "ignore_if_empty":datasource["ignore_if_empty"]
                        }
                        if "field_strategy" in sourcelayer:
                            layer["field_strategy"]  = sourcelayer["field_strategy"]
                            del sourcelayer["field_strategy"]
                        if sourcelayer["format"]["name"] in ["geojson","json"]:
                            layer["layer"] = getBaseDatafileName(sourcelayer["datasource"][1],False)
                        else:
                            layer["layer"] = metadata["layer"]

                        if "default_geometry_type" in datasource:
                            layer["default_geometry_type"] = datasource["default_geometry_type"]
                        layers.append(layer)

        del loadedDatasources

        #remove layers which do not include spatial data
        if layers:
            index1 = len(layers) - 1
            while index1 >= 0:
                index2 = len(layers[index1]["sourcelayers"]) - 1
                while index2 >= 0:
                    if not layers[index1]["sourcelayers"][index2].get("meta"):
                        #no spatial data
                        del layers[index1]["sourcelayers"][index2]
                    elif layers[index1]["ignore_if_empty"] and layers[index1]["sourcelayers"][index2]["meta"].get("features",0) == 0:
                        #no features
                        del layers[index1]["sourcelayers"][index2]
                    index2 -= 1
                if len(layers[index1]["sourcelayers"]) == 0:
                    #no spatial data
                    del layers[index1]
                index1 -= 1

        if not layers:
            raise Exception("No spatial data found.")

        #import ipdb;ipdb.set_trace()
        #determine the output layer name
        if fmt["multilayer"]:
            names = {}
            #first get the shortest name and check whether it is unique
            for layer in layers:
                if layer.get("layer"):
                    name = layer["layer"]
                else:
                    name = None
                    for srcLayer in layer["sourcelayers"]:
                        if srcLayer["meta"]["format"]["name"] not in ["geojson","json"]:
                            name = srcLayer["layer"]
                            break
                        elif not name:
                            #use the file name as the layer name if format is geojson or json
                            name = getBaseDatafileName(srcLayer["datasource"][1],False)
                
                names[name] = names.get(name,0) + 1
                layer["layer"] = name

            #append the file path to the name if shortest name is duplicate.
            for layer in layers:
                name = layer["layer"]
                if names.get(name,1) > 1:
                    sourcename = getBaseDatafileName(layer["sourcelayers"][0]["datasource"][1],True)
                    if sourcename.endswith(name):
                        sourcename = os.path.dirname(sourcename)
                    if sourcename and sourcename != "/":
                       sourcename = sourcename.replace("/","_")
                       layer["layer"] = "{}_from_{}".format(name,sourcename)

            del names
        else:
            for layer in layers:
                if not layer.get("layer"):
                    name = None
                    for srcLayer in layer["sourcelayers"]:
                        if srcLayer["meta"]["format"]["name"] not in ["geojson","json"]:
                            name = srcLayer["layer"]
                            break
                        elif not name:
                            #use the file name as the layer name if format is geojson or json
                            name = getBaseDatafileName(srcLayer["datasource"][1],False)
                    layer["layer"] = name

        #import ipdb;ipdb.set_trace()
        #determine the output datasource name
        if fmt["multilayer"]:
            for layer in layers:
                #target format support multiple layer, use the output file name or the first source layer's file name as the source name
                if filename:
                    layer["sourcename"] = filename
                else:
                    layer["sourcename"] = getBaseDatafileName(layer["sourcelayers"][0]["file"])
        else:
            names = {}
            #first get the prefered file name and check whether it is unique
            for layer in layers:
                if not layer.get("sourcename"):
                    layer["sourcename"] = getBaseDatafileName(layer["sourcelayers"][0]["datasource"][1],True)
                names[layer["sourcename"]] = names.get(layer["sourcename"],0) + 1

            #if all the sourcename are same, then no need to use separate folder, set the sourcename to None
            if len(names) <= 1:
                for layer in layers:
                    layer["sourcename"] = None


            #append the layer name to the file name if the prefered name is duplicate.
            #for layer in layers:
            #    if names[layer["sourcename"]] > 1:
            #        layer["sourcename"] = os.path.join(layer["sourcename"],layer["layer"])
            #        pass
            
            del names

        #determine the output srs
        srss = {}
        for layer in layers:
            if srss.get(layer["sourcename"]):
                layer["srs"] = srss[layer["sourcename"]]
            elif layer.get("srs"):
                srss[layer["sourcename"]] = layer["srs"]
            elif outputSrs:
                layer["srs"] = outputSrs
                srss[layer["sourcename"]] = layer["srs"]
            else:
                layer["srs"] = None
                for l in layer["sourcelayers"]:
                    if l["meta"]["srs"]:
                        layer["srs"] = l["meta"]["srs"]
                        srss[layer["sourcename"]] = layer["srs"]
                        break
        del srss
        
        # changing coordinates to EPSG:4326
        for layer in layers:
            layer['srs'] = None
            if(layer['sourcelayers']):
                for l in layer['sourcelayers']:
                    l['meta']['srs'] = None
                    l['srs'] = None        
                    
        #convert and union the layers
        outputdir = os.path.join(workdir,"output")
        os.makedirs(outputdir, exist_ok=True)

        unsupported_layers = []
        #print "{}".format(layers)
        for layer in layers:
            for sourcelayer in layer["sourcelayers"]:
                if sourcelayer["meta"]["geometry"] not in SUPPORTED_GEOMETRY_TYPES and sourcelayer["meta"]["geometry"].find("UNKNOWN") < 0:
                    unsupported_layers.append("{}({})".format(sourcelayer["layer"],sourcelayer["meta"]["geometry"]))

        if len(unsupported_layers) > 0:
            raise Exception("Unsupported geometry type ({}).".format(str(unsupported_layers)))

        outputFiles = []

        vrtdir = os.path.join(workdir,"vrt")
        os.makedirs(vrtdir, exist_ok=True)

        #import ipdb;ipdb.set_trace()
        for layer in layers:
            #populate the vrt file
            if layer.get("sourcename",None):
                vrtFile = os.path.join(vrtdir,layer["sourcename"],"{}.vrt".format(layer["layer"]))
            else:
                vrtFile = os.path.join(vrtdir,"{}.vrt".format(layer["layer"]))
            if not os.path.exists(os.path.dirname(vrtFile)):
                os.makedirs(os.path.dirname(vrtFile))
                      
            if layer.get("geometry_column"):
                layer["geometry_field"] = {"name":layer["geometry_column"]["name"]}

            for slayer in layer["sourcelayers"]:
                #populate fields
                if slayer.get("fields"):
                    index = len(slayer["fields"]) - 1
                    while index >= 0:
                        try:
                            slayer["fields"][index] = [slayer["fields"][index]["name"]] + next(o for o in slayer["meta"]["fields"] if o[0].lower() == slayer["fields"][index]["src"].lower())
                        except StopIteration:
                            #field does not exist, remove it
                            del slayer["fields"][index]
                        index -= 1
                    if len(slayer["fields"]) == 0:
                            del slayer["fields"]
                #populate geometry column
                if layer.get("geometry_column"):
                    slayer["geometry_field"] = {"name":layer["geometry_column"]["name"]}
                    if slayer["meta"].get("geometry_column"):
                        slayer["geometry_field"]["src"] = slayer["meta"]["geometry_column"]


            vrt = UNIONLAYERS_TEMPLATE.render(layer)

            with open(vrtFile,"w") as f:
                f.write(vrt)


            os.listdir(os.path.dirname(vrtFile))
            vrt = None
            if fmt["multitype"]:
                outputDatasource = getOutputDatasource(outputdir,fmt,layer)
                if outputDatasource in outputFiles:
                    cmd = ["ogr2ogr","-skipfailures","-update" ,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                else:
                    cmd = ["ogr2ogr","-skipfailures" ,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile] 
                    outputFiles.append(outputDatasource)
                if "ogr2ogr_arguments" in fmt:
                    index = 1
                    for arg in fmt["ogr2ogr_arguments"]:
                        cmd.insert(index,arg)
                        index += 1
                #print " ".join(cmd)
                # subprocess.check_call(cmd)
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                if result.stderr:
                    raise Exception(str(result.stderr))
            else:
                #get all geometry types in the source layer list
                srcTypes = []
                index = len(layer["sourcelayers"]) - 1
                while index >= 0:
                    srcLayer = layer["sourcelayers"][index]
                    if srcLayer["meta"]["geometry"] in SUPPORTED_GEOMETRY_TYPES:
                        if srcLayer["meta"]["geometry"] not in srcTypes:
                            srcTypes.append(srcLayer["meta"]["geometry"])
                    else:
                        for t in SUPPORTED_GEOMETRY_TYPES:
                            if getFeatureCount(srcLayer["datasource"][0],srcLayer["meta"]["layer"],t) and t not in srcTypes:
                                srcTypes.append(t)

                    index -= 1

                if len(srcTypes) == 1:
                    if "default_geometry_type" in layer:
                        del layer["default_geometry_type"]
                else:
                    hasEmptyFeatures = False
                    index = len(layer["sourcelayers"]) - 1
                    while index >= 0:
                        srcLayer = layer["sourcelayers"][index]
                        index -= 1
                        if getFeatureCount(srcLayer["datasource"][0],srcLayer["meta"]["layer"],"EMPTY") > 0:
                            hasEmptyFeatures = True
                            break

                    if hasEmptyFeatures:
                        if layer.get("default_geometry_type") == "auto":
                            for t in SUPPORTED_GEOMETRY_TYPES:
                                if t in srcTypes:
                                    layer["default_geometry_type"] = t
                                    break
                        
                        elif layer.get("default_geometry_type"):
                            if layer.get("default_geometry_type") not in srcTypes:
                                srcTypes.append("default_geometry_type")
                        else:
                            srcTypes.append("EMPTY")
    
                    elif "default_geometry_type" in layer:
                        del layer["default_geometry_type"]


                if len(srcTypes) == 1:
                    #has only one geometry type
                    outputDatasource = getOutputDatasource(outputdir,fmt,layer)
                    if outputDatasource in outputFiles:
                        cmd = ["ogr2ogr","-skipfailures","-update" ,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                    else:
                        cmd = ["ogr2ogr","-skipfailures","-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                        outputFiles.append(outputDatasource)
                    
                    #print " ".join(cmd)
                    if "ogr2ogr_arguments" in fmt:
                        index = 1
                        for arg in fmt["ogr2ogr_arguments"]:
                            cmd.insert(index,arg)
                            index += 1
                    subprocess.check_call(cmd) 
                else:
                    for t in srcTypes:
                        where = ("OGR_GEOMETRY IS NULL" if t == "EMPTY" else ("OGR_GEOMETRY='{}' OR OGR_GEOMETRY IS NULL" if layer.get("default_geometry_type") == t else "OGR_GEOMETRY='{}'")).format(t)
                        outputDatasource = getOutputDatasource(outputdir,fmt,layer,t)
                        if outputDatasource in outputFiles:
                            cmd = ["ogr2ogr","-skipfailures","-update","-where", where,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                        else:
                            cmd = ["ogr2ogr","-skipfailures","-where", where,"-t_srs",(layer.get("srs") or "EPSG:4326"), "-f", fmt["format"],outputDatasource, vrtFile]
                            outputFiles.append(outputDatasource)

                        #print " ".join(cmd)
                        if "ogr2ogr_arguments" in fmt:
                            index = 1
                            for arg in fmt["ogr2ogr_arguments"]:
                                cmd.insert(index,arg)
                                index += 1
                        subprocess.check_call(cmd) 
        
        #import ipdb;ipdb.set_trace()
        #check whether outputfile is a single file or multiple files.
        #if a single file is returned, outputfile will be the file ; otherwise outputfile will be none
        outputfile = None
        checkfiles = [outputdir]
        while len(checkfiles) > 0:
            checkfile = checkfiles.pop()
            if os.path.isdir(checkfile):
                dirlist = os.listdir(checkfile)
                checkfiles.extend([os.path.join(checkfile,f) for f in dirlist])
            elif outputfile:
                outputfile = None
                break
            else:
                outputfile = checkfile
        del checkfiles

        #import ipdb;ipdb.set_trace()
        if outputfile:
            #only one file is returned.
            filemime = fmt["mime"]
            if filename:
                outputfilename = os.path.basename("{}{}".format(filename,fmt["fileext"]))
            else:
                outputfilename = os.path.basename(outputfile)
        else:
            #multiple files are returned, use zip to compress all files into one file.
            ct = "application/zip"
            if filename:
                zipfile = os.path.join(workdir,filename)
            else:
                zipfile = os.path.join(workdir,getBaseDatafileName(layer["sourcelayers"][0]["file"]))
            zipfile = zipfile + fmt["fileext"]
            shutil.make_archive(zipfile, 'zip', outputdir)
            outputfile = "{}.zip".format(zipfile)
            filemime = "application/zip"
            outputfilename = os.path.basename(outputfile)

        output = open(outputfile)
        #bottle.response.set_header("Content-Type", filemime)
        #bottle.response.set_header("Content-Disposition", "attachment;filename='{}'".format(os.path.basename(outputfilename)))
        resp = {'outputfile': outputfile, 'outputfilename': outputfilename,'filemime':filemime, "output": output}
        return resp
        #return output
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #bottle.response.status = 400
        #bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        resp = {'output' :  str(e) , 'filemime': 'text/plain' , 'outputfile': None, "outputfilename": "traceback_error.html"}
        return resp
        #eturn traceback.format_exception_only(exc_type,exc_value)
    finally:
        try:
            #print "workdir = {}".format(workdir)
            #shutil.rmtree(workdir)
            pass
        except:
            pass
