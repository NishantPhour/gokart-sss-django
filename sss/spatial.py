#import os
import sys
import requests
import json
import pyproj
import traceback
import math
#from datetime import datetime
from multiprocessing import Process, Pipe
import time

from shapely.geometry import shape,MultiPoint,Point,mapping
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.collection import GeometryCollection
from shapely.geometry.base import BaseGeometry
from shapely import ops
from shapely.validation import make_valid as shapely_make_valid
from functools import partial
from sss.models import SpatialDataCalculation, CRSSettings
from sss.sss_gdal import SUPPORTED_CRS
from django.conf import settings
from sss import kmi
from pyproj import CRS

proj_aea = lambda geometry: pyproj.Proj("+proj=aea +lat_1=-17.5 +lat_2=-31.5 +lat_0=0 +lon_0=121 +x_0=5000000 +y_0=10000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs")

def is_geographic_crs(crs_code):
    """Check if a given CRS uses degrees (latitude/longitude) instead of meters."""
    crs = CRS(crs_code)
    return crs.is_geographic

def exportGeojson(feat,fname):
    if isinstance(feat,BaseGeometry):
        geojson = {
            "type":"FeatureCollection",
            "features":[
                {
                    "type":"Feature",
                    "geometry":mapping(feat),
                    "properties":{}
                }
            ]
        }
    elif isinstance(feat,tuple):
        geojson = {
            "type":"FeatureCollection",
            "features":[
                {
                    "type":"Feature",
                    "geometry":mapping(feat[0]),
                    "properties":feat[1] or {}
                }
            ]
        }
    elif isinstance(feat,list):
        features = []
        geojson = {
            "type":"FeatureCollection",
            "features":features
        }
        for f in feat:
            if isinstance(f,BaseGeometry):
                features.append({
                    "type":"Feature",
                    "geometry":mapping(f),
                    "properties":{}
                })
            elif isinstance(f,tuple):
                features.append({
                    "type":"Feature",
                    "geometry":mapping(f[0]),
                    "properties":f[1] or {}
                })
            else:
                raise Exception("Unsupported type({}.{})".format(f.__class__.__module__,f.__class__.__name__))
    else:
        raise Exception("Unsupported type({}.{})".format(feat.__class__.__module__,feat.__class__.__name__))


    with open(fname,'w') as f:
        f.write(json.dumps(geojson,indent=True))

    return fname

proj_wgs84 = pyproj.Proj(init='epsg:4326')
def buffer(lon, lat, meters,resolution=16):
    """
    Create a buffer around a point
    """
    # Azimuthal equidistant projection
    aeqd_proj = '+proj=aeqd +lat_0={} +lon_0={} +x_0=0 +y_0=0'
    project = partial(
        pyproj.transform,
        pyproj.Proj(aeqd_proj.format(lat, lon)),
        proj_wgs84)
    buf = Point(0, 0).buffer(meters,resolution=resolution)  # distance in metres
    return ops.transform(project, buf).exterior.coords[:]


def getShapelyGeometry(feature):
    if not feature["geometry"]:
        return None
    elif feature["geometry"]["type"] == "GeometryCollection":
        return GeometryCollection([shape(g) for g in feature["geometry"]["geometries"]])
    else:
        return shape(feature["geometry"])


def repairGeometry(geometry):
    if not geometry or geometry.is_valid:
        return geometry

    try:
        repaired = shapely_make_valid(geometry)
    except Exception:
        repaired = geometry.buffer(0)

    if repaired and not repaired.is_empty:
        return repaired
    return geometry


def repairFeatureGeometry(feature):
    geometry = getShapelyGeometry(feature)
    if not geometry or geometry.is_valid:
        return feature

    repaired = repairGeometry(geometry)
    feature["geometry"] = mapping(repaired)
    return feature





# this tranform function is used for more accurate area calculation, currently supports {aea,EPSG:3577}
def transform(geometry,src_proj="EPSG:4326",target_proj='aea'):
    if src_proj == target_proj:
        return geometry
    elif target_proj != 'aea':
        transformer = pyproj.Transformer.from_crs(src_proj, target_proj, always_xy=True)
        projected_geometry = ops.transform(transformer.transform, geometry)
        return projected_geometry
    else:
        if src_proj == 'aea':
            src_proj = proj_aea(geometry)
        else:
            src_proj = pyproj.Proj(init=src_proj)

        if target_proj == 'aea':
            target_proj = proj_aea(geometry)
        else:
            target_proj = pyproj.Proj(init=target_proj)

        return ops.transform(
            partial(
                pyproj.transform,
                src_proj,
                #pyproj.Proj(proj="aea",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
                #use projection 'Albers Equal Conic Area for WA' to calcuate the area
                target_proj
            ),
            geometry
        )

    
def getGeometryArea(geometry,unit):
    """
    Get polygon's area
    """
    data = geometry.area
    if unit == "ha" :
        return data / 10000.00
    elif unit == "km2":
        return data / 1000000.00
    else:
        return data
    
    



degrees2radians = math.pi / 180
radians2degrees = 180 /math.pi
def getBearing(p1,p2):
    lon1 = degrees2radians * p1.x
    lon2 = degrees2radians * p2.x
    lat1 = degrees2radians * p1.y
    lat2 = degrees2radians * p2.y
    a = math.sin(lon2 - lon1) * math.cos(lat2)
    b = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1);

    bearing = radians2degrees * math.atan2(a, b);
    return bearing if bearing >= 0 else bearing + 360

directions = {
    4:[360/4,math.floor(360 / 8 * 100) / 100,["N","E","S","W"]],
    8:[360/8,math.floor(360 / 16 * 100) / 100,["N","NE","E","SE","S","SW","W","NW"]],
    16:[360/16,math.floor(360 / 32 * 100) / 100,["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]],
    32:[360/32,math.floor(360 / 64 * 100) / 100,["N","NbE","NNE","NEbN","NE","NEbE","ENE","EbN","E","EbS","ESE","SEbE","SE","SEbS","SSE","SbE","S","SbW","SSW","SWbS","SW","SWbW","WSW","WbS","W","WbN","WNW","NWbW","NW","NWbN","NNW","NbW"]],
}

def getDirection(bearing,mode = 16):
    mode = mode or 16
    if mode not in directions:
        mode = 16

    index = int((math.floor(bearing / directions[mode][0])  + 0 if ((round(bearing % directions[mode][0],2) <= directions[mode][1])) else 1) % mode)
    return directions[mode][2][index]

def getDistance(p1,p2,unit="m",p1_proj="EPSG:4326",p2_proj="EPSG:4326"):
    if p1_proj == 'aea':
        p1_aea = p1
    else:
        p1_aea = ops.transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init=p1_proj),
                #pyproj.Proj(proj="aea",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
                #use projection 'Albers Equal Conic Area for WA' to calcuate the area
                proj_aea(p1)
            ),
            p1
        )

    if p2_proj == 'aea':
        p2_aea = p2
    else:
        p2_aea = ops.transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init=p2_proj),
                #pyproj.Proj(proj="aea",lat1=geometry.bounds[1],lat2=geometry.bounds[3])
                #use projection 'Albers Equal Conic Area for WA' to calcuate the area
                proj_aea(p2)
            ),
            p2
        )

    data = p1_aea.distance(p2_aea)
    if unit == "km" :
        return data / 1000.00
    else:
        return data

#return polygon or multipolygons if have, otherwise return None
def extractPolygons(geom):
    if not geom:
        return None
    elif isinstance(geom,Polygon) or isinstance(geom,MultiPolygon):
        return geom
    elif isinstance(geom,GeometryCollection):
        result = None
        for g in geom.geoms:
            p = extractPolygons(g)
            if not p:
                continue
            elif not result:
                result = p
            elif isinstance(result,MultiPolygon):
                result = [geom1 for geom1 in result.geoms]
                if isinstance(p,Polygon):
                    result.append(p)
                    result = MultiPolygon(result)
                else:
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPolygon(result)
            else:
                if isinstance(p,Polygon):
                    result = MultiPolygon([result,p])
                else:
                    result = [result]
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPolygon(result)
        return result
    else:
        return None

def extractPoints(geom):
    if isinstance(geom,Point) or isinstance(geom,MultiPoint):
        return geom
    elif isinstance(geom,GeometryCollection):
        result = None
        for g in geom.geoms:
            p = extractPoints(g)
            if not p:
                continue
            elif not result:
                result = p
            elif isinstance(result,MultiPoint):
                result = [geom1 for geom1 in result.geoms]
                if isinstance(p,Point):
                    result.append(p)
                    result = MultiPoint(result)
                else:
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPoint(result)
            else:
                if isinstance(p,Point):
                    result = MultiPoint([result,p])
                else:
                    result = [result]
                    for geom1 in p.geoms:
                        result.append(geom1)
                    result = MultiPoint(result)
        return result
    else:
        return None

def retrieveFeatures(url,session_cookies,layerid):
        auth_request = kmi.get_auth(layerid)
        res = requests.get(url,
                           verify=kmi.is_kb_layer(layerid),
                           auth=auth_request,
                           #cookies=session_cookies
                            )   
        res.raise_for_status()
        return res.json()

def checkOverlap(session_cookies,feature,options,logfile):
    # needs gdal 1.10+
    layers = options["layers"]
    geometry = extractPolygons(getShapelyGeometry(feature))
    if not geometry :
        return

    features = {}
    #retrieve all related features from layers
    for layer in layers:
        kmiserver = kmi.get_kmiserver(layerid=layer["layerid"])
        layer["kmiservice"] = kmiserver
        if layer.get('cqlfilter'):
            layer_url="{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=BBOX({},{},{},{},{}) AND {}".format(kmiserver,layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2],layer['cqlfilter'])
        else:
            layer_url="{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&bbox={},{},{},{}".format(kmiserver,layer["layerid"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2])
        features[layer["id"]] = retrieveFeatures(layer_url, session_cookies, layer["layerid"])["features"]

        for layer_feature in features[layer["id"]]:
            layer_geometry = getShapelyGeometry(layer_feature)
            layer_feature["geometry"] = layer_geometry

    #check whether the features from different layers are overlap or not
    layergroup_index1 = 0
    while layergroup_index1 < len(layers) - 1:
        layer1 = layers[layergroup_index1]
        layergroup_index1 += 1
        layer_features1 = features[layer1["id"]]

        #check whether layer's features are overlap or not.
        feature_index1 = 0
        while feature_index1 < len(layer_features1):
            feature1 = layer_features1[feature_index1]
            feature_index1 += 1
            feature_geometry1 = feature1["geometry"]
            if not isinstance(feature_geometry1,Polygon) and not isinstance(feature_geometry1,MultiPolygon):
                continue

            layergroup_index2 = layergroup_index1
            while layergroup_index2 < len(layers):
                layer2 = layers[layergroup_index2]
                layergroup_index2 += 1
                layer_features2 = features[layer2["id"]]
                feature_index2 = 0

                while feature_index2 < len(layer_features2):
                    feature2 = layer_features2[feature_index2]
                    feature_index2 += 1
                    feature_geometry2 = feature2["geometry"]
                    feature_geometry1 = feature1["geometry"]
                    if not isinstance(feature_geometry2,Polygon) and not isinstance(feature_geometry2,MultiPolygon):
                        continue
                    intersections = extractPolygons(feature_geometry1.intersection(feature_geometry2))
                    if not intersections:
                        continue

                    layer1_pk = layer1.get("primary_key")
                    layer2_pk = layer2.get("primary_key")

                    if layer1_pk:
                        if isinstance(layer1_pk,str):
                            feat1 = "{}({}={})".format(layer1["layerid"],layer1_pk,feature1["properties"][layer1_pk])
                        else:
                            feat1 = "{}({})".format(layer1["layerid"],", ".join(["{}={}".format(k,v) for k,v in feature1["properties"].items() if k in layer1_pk ]))
                    else:
                        feat1 = "{}({})".format(layer1["layerid"],json.dumps(feature1["properties"]))

                    if layer2_pk:
                        if isinstance(layer2_pk,str):
                            feat2 = "{}({}={})".format(layer2["layerid"],layer2_pk,feature2["properties"][layer2_pk])
                        else:
                            feat2 = "{}({})".format(layer2["layerid"],", ".join(["{}={}".format(k,v) for k,v in feature2["properties"].items() if k in layer2_pk ]))
                    else:
                        feat2 = "{}({})".format(layer2["layerid"],json.dumps(feature2["properties"]))

                    msg = "intersect({}, {}) = {} ".format( feat1,feat2, intersections )
                    with open(logfile,"a") as f:
                        f.write(msg)
                        f.write("\n")


def calculateArea(feature,kmiserver,session_cookies,options):
    """
    return:{
        status {
             "invalid" : invalid message;
             "failed" : failed message;
             "overlapped" : overlap message

        }
        data: {
            total_area: 100   //exist if status_code = 1
            other_area: 10    //exist if status_code = 1 and len(layers) > 0
            layers: {   //exist if status_code = 1 and len(layers) > 0
                layer id: {
                    total_area: 12
                    areas:[
                        {area:1, properties:{
                            name:value
                        }}
                    ]
                }
            }
        }
    }
    The reason to calculate the area in another process is to releace the memory immediately right after area is calculated.
    """
    if not settings.CALCULATE_AREA_IN_SEPARATE_PROCESS:
        return  _calculateArea(feature,kmiserver,session_cookies,options,False)

    parent_conn,child_conn = Pipe(True)
    p = Process(target=calculateAreaInProcess,args=(child_conn,))
    p.daemon = True
    p.start()
    parent_conn.send([feature,kmiserver,session_cookies,options])
    result = parent_conn.recv()
    parent_conn.close()
    #p.join()
    #print("{}:get the area result from other process".format(datetime.now()))
    return result


def calculateAreaInProcess(conn):
    feature,kmiserver,session_cookies,options = conn.recv()
    result = _calculateArea(feature,kmiserver,session_cookies,options,True)

    if "overlap_logfile" in result:
        overlapLogfile = result["overlap_logfile"]
        del result["overlap_logfile"]
    else:
        overlapLogfile = None
    conn.send(result)
    conn.close()
    #print("{}:Calculating area finiahed".format(datetime.now()))
    #import time
    #time.sleep(30)
    #if overlapLogfile:
    #    try:
    #        if os.path.exists(overlapLogfile):
    #            os.remove(overlapLogfile)
    #    except:
    #        pass
    #    checkOverlap(session_cookies,feature,options,overlapLogfile)
    #print("{}:subprocess finished".format(datetime.now()))

def calculateFeatureArea(feature,src_proj="EPSG:4326",unit='ha'):
    return calculateGeometryArea(getShapelyGeometry(feature),src_proj=src_proj,unit=unit)

def calculateGeometryArea(geometry,src_proj="EPSG:4326",unit='ha'):
    geometry = extractPolygons(geometry)
    if not geometry :
        return 0

    valid,msg = geometry.check_valid
    if not valid:
        print("geometry is invalid.{}", msg)

    # geometry_aea = transform(geometry,src_proj=src_proj,target_proj='aea')

    return  getGeometryArea(geometry,unit)


def _calculateArea(feature,kmiserver,session_cookies,options,run_in_other_process=False):
    # needs gdal 1.10+
    layers = options["layers"]
    unit = options["unit"] or "ha"
    overlap = options["layer_overlap"] or False
    merge_result = options.get("merge_result",False)

    area_data = {}
    status = {}
    result = {"status":status,"data":area_data}

    total_area = 0
    total_layer_area = 0
    geometry = repairGeometry(getShapelyGeometry(feature))
    geometry = extractPolygons(geometry)
    geometry = extractPolygons(repairGeometry(geometry))
    if not geometry :
        area_data["total_area"] = 0
        return result

    #before calculating area, check the polygon first.
    #if polygon is invalid, throw exception
    #valid,msg = geometry.check_valid
    #if not valid:
    #    status["invalid"] = msg
    
    TRANSFORM_TO_ORIGINAL_CRS = False # Set this to true if want to transfer the geometry to the original CRS of the feature before calculating area, else it will use the CRS specified in the CRSSettings

    if TRANSFORM_TO_ORIGINAL_CRS:
        feature_crs = feature['properties'].get('crs', None)
        if(feature_crs):
            # Check if the source CRS is supported
            if feature_crs not in SUPPORTED_CRS.keys():
                status["invalid"] = "Unsupported source CRS: {}".format(feature_crs)
                return result
            else:
                # Get the source CRS from the supported CRS
                feature_crs_epsg = SUPPORTED_CRS[feature_crs]
                if feature_crs_epsg.lower().startswith("epsg") and is_geographic_crs(feature_crs_epsg): # If the source CRS is geographic (degrees), we will transform it to the target projection specified in the CRSSettings
                    selected_crs_settings = CRSSettings.objects.first()
                    target_projection = selected_crs_settings.crs
                else:
                    target_projection = feature_crs_epsg  # Use original CRS for projected systems

                transformed_geometry = transform(geometry, target_proj=target_projection)

        else:
            # Default to AEA if no CRS is provided
            target_projection = 'aea'
            transformed_geometry = transform(geometry,target_proj=target_projection)
    else:
        selected_crs_settings = CRSSettings.objects.first()
        target_projection = selected_crs_settings.crs
        transformed_geometry = transform(geometry, target_proj=target_projection)

    try:
        # calculate the area of the geometry directly on the wgs84 sphere
        area_data["total_area"] = getGeometryArea(transformed_geometry, unit=unit)
    except Exception as error:
        traceback.print_exc()
        if "invalid" in status:
            status["failed"] = "Calculate total area failed.{}".format("\r\n".join(status["invalid"]))
        else:
            status["failed"] = "Calculate total area failed.{}".format(traceback.format_exception_only(type(error),error))

        return result

    if not layers:
        return result

    if settings.EXPORT_CALCULATE_AREA_FILES_4_DEBUG:
        #export geometry for debug
        properties = feature["properties"]
        properties.update({"area":area_data["total_area"]})
        exportGeojson((transformed_geometry,properties),"/tmp/feature.geojson")

    for layer in layers:
        if "layerid" not in layer and "id" not in layer:
            raise Exception("Both 'id' and 'layerid' are missing in layer declaration")
        elif "layerid" not in layer:
            layer["layerid"] = layer["id"]
        elif "id" not in layer:
            layer["id"] = layer["layerid"]
        layer["kmiservice"] = kmi.get_kmiserver(layerid=layer["layerid"])
    
    area_data["layers"] = {}
    areas_map = {} if merge_result else None
    for layer in layers:
        try:
            kmi_server = layer["kmiservice"]
            layer_area_data = []
            total_layer_area = 0
            area_data["layers"][layer["id"]] = {"areas":layer_area_data}

            if layer.get('cqlfilter'):
                layer_url="{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=BBOX({},{},{},{},{}) AND {}".format(kmi_server,layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2],layer['cqlfilter'])
            else:
                layer_url="{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&bbox={},{},{},{}".format(kmi_server,layer["layerid"],geometry.bounds[1],geometry.bounds[0],geometry.bounds[3],geometry.bounds[2])

            layer_features = retrieveFeatures(layer_url,session_cookies,layer["layerid"])["features"]

            if settings.EXPORT_CALCULATE_AREA_FILES_4_DEBUG:
                #export intersected areas for debug
                intersected_features = []
                intersected_layer_features = []

            for layer_feature in layer_features:
                layer_geometry = getShapelyGeometry(layer_feature)
                if not layer_geometry.is_valid:
                   layer_geometry = layer_geometry.buffer(0)      #Times out if reserves is a single massive poly
                  #  return {"status":"failed","data":"invalid polygon in tenure layer, probably the other_tenures layer"}
                layer_geometry = transform(layer_geometry,target_proj=target_projection)
                if not isinstance(layer_geometry,Polygon) and not isinstance(layer_geometry,MultiPolygon):
                    continue
                intersections = extractPolygons(transformed_geometry.intersection(layer_geometry))

                if not intersections:
                    continue

                layer_feature_area_data = None
                #try to get the area data from map
                if merge_result:
                    area_key = []
                    for key,value in layer["properties"].items():
                        area_key.append(layer_feature["properties"][value])

                    area_key = tuple(area_key)
                    layer_feature_area_data = areas_map.get(area_key)

                if not layer_feature_area_data:
                     #map is not enabled,or data does not exist in map,create a new one
                    layer_feature_area_data = {"area":0}
                    for key,value in layer["properties"].items():
                        layer_feature_area_data[key] = layer_feature["properties"][value]
                    layer_area_data.append(layer_feature_area_data)

                    if merge_result:
                        #save it into map
                        areas_map[area_key] = layer_feature_area_data

                # Calculate the area of the intersections
                #This area is calculated on AEA projection (Reason: the intersections returned from the KMI server are most accurate when projected on AEA as compared to directly calculating it on WGS84)
                feature_area = getGeometryArea(intersections, unit=unit)
                layer_feature_area_data["area"] += feature_area
                total_layer_area  += feature_area

                if settings.EXPORT_CALCULATE_AREA_FILES_4_DEBUG:
                    #export intersected areas for debug
                    properties = layer_feature["properties"]
                    properties.update({"area":feature_area})
                    intersected_features.append((intersections,properties))
                    intersected_layer_features.append((layer_geometry,properties))

            if settings.EXPORT_CALCULATE_AREA_FILES_4_DEBUG:
                #export intersected areas for debug
                if intersected_features:
                    for feat in intersected_features:
                        feat[1].update({"total_area":total_layer_area})
                    exportGeojson(intersected_features,'/tmp/feature_area_{}_intersection.geojson'.format(layer["id"]))
                    exportGeojson(intersected_layer_features,'/tmp/feature_area_{}.geojson'.format(layer["id"]))


            area_data["layers"][layer["id"]]["total_area"] = total_layer_area
            total_area += total_layer_area
            if not overlap and total_area >= area_data["total_area"] :
                break

        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exc()
            status["failed"] = "Calculate intersection area between fire boundary and layer '{}' failed.{}".format(layer["layerid"] or layer["id"],traceback.format_exception_only(exc_type,exc_value))

            break

    if "failed" in status:
        #calcuating area failed
        return result

    if not overlap :
        # sum of interstection area needs to be compared with the AEA projection of geometry (transformed_geometry) for better accuracy
        area_data["other_area"] = area_data["total_area"] - total_area
        if area_data["other_area"] < -0.01: #tiny difference is allowed.
            #some layers are overlap
            if not settings.CHECK_OVERLAP_IF_CALCULATE_AREA_FAILED:
                status["overlapped"] = "The sum({0}) of the burning areas in individual layers are ({2}) greater than the total burning area({1}).\r\n The features from layers({3}) are overlaped, please check.".format(round(total_area,2),round(area_data["total_area"],2),round(math.fabs(area_data["other_area"]),2),", ".join([layer["id"] for layer in layers]))
            else:
                filename = "/tmp/overlap_{}.log".format(feature["properties"].get("id","feature"))
                status["overlapped"] = "Features from layers are overlaped,please check the log file in server side '{}'".format(filename)
                if run_in_other_process:
                    result["overlap_logfile"] = filename
                else:
                    checkOverlap(session_cookies,feature,options,filename)

    return result

def layermetadata(layer):
    if not layer.get("_layermetadata"):
        layer["_layermetadata"] = kmi.get_layermetadata(layer["layerid"],kmiserver=layer["kmiservice"])
    return layer["_layermetadata"]

def layerdefinition(layer):
    if not layer.get("_layerdefinition"):
        layerdefinition = kmi.get_layerdefinition(layer["layerid"],kmiserver=layer["kmiservice"])
        layer["_layerdefinition"] = layerdefinition
    else:
        layerdefinition = layer["_layerdefinition"]

    if not layerdefinition["geometry_property"]:
        if layerdefinition["geometry_property_msg"]:
            raise Exception(layerdefinition["geometry_property_msg"])
        elif not layerdefinition["geometry_properties"]:
            raise Exception("The layer '{}' is not a spatial layer".format(layer["layerid"]))
        else:
            raise Exception("Failed to identify the geometry property of the layer '{}'".format(layer["layerid"]))

    return layerdefinition


def getFeature(feature,kmiserver,session_cookies,options):
    """
    options:{
        format: properties or geojson//optional default is properties
        action: getFeature or getIntersectedFeatures or getClosestFeature
        layers:[
            {
                id:     //if missing, use 'layerid' as id
                layerid: //layerid in kmi, in most cases, layerid is equal with id, if missing, use 'id' as layerid
                kmiservice: //optinoal,
                properties:{  //optional
                    name:column in dataset
                }
            },
            ...
        ]

    }
    getFeature result:[
        {
            id:
            layer:
            failed:  message if failed; otherwise is null
            properties: {
                name:value
            }
        },
    ]
    """
    # needs gdal 1.10+
    layers = options["layers"]
    #check whether layers is not empty
    if not layers:
        raise Exception("Layers must not be empty.")
    #check whether layers is list
    if not isinstance(layers,(list,tuple)):
        raise Exception("Layers must be list type.")

    #layers must be list of layers
    if  not isinstance(layers,(list,tuple)):
        layers = [layers]
    for layer in layers:
        if "layerid" not in layer and "id" not in layer:
            raise Exception("Both 'id' and 'layerid' are missing in layer declaration")
        elif "layerid" not in layer:
            layer["layerid"] = layer["id"]
        elif "id" not in layer:
            layer["id"] = layer["layerid"]
        layer["kmiservice"] = kmi.get_kmiserver(layerid=layer["layerid"])

    get_feature_data = {"id":None,"layer":None,"failed":None}

    geometry = getShapelyGeometry(feature)
    try:
        for layer in layers:
            if not layer or not layer.get("kmiservice") or not layer["layerid"]:
                continue
            kmiserver = layer["kmiservice"]

            if layer.get('check_bbox'):
                #check whether feature is in layer's bbox
                layer_bbox = layermetadata(layer).get("latlonBoundingBox_EPSG:4326") or layermetadata(layer).get("latlonBoundingBox")
                if not layer_bbox:
                    get_feature_data["failed"] = "Can't find layer({})'s bounding box for epsg:4326".format(layer["layerid"])
                    break
                #buffered_bbox is  lonlatboundingbox
                if layer.get("buffer") and isinstance(geometry,Point):
                    checking_bbox = Polygon(buffer(geometry.x,geometry.y,layer["buffer"][-1] if isinstance(layer["buffer"],(list,tuple)) else layer["buffer"],resolution=1)).bounds
                else:
                    checking_bbox = geometry.bounds

                if checking_bbox[2] < layer_bbox[1] or checking_bbox[0] > layer_bbox[3] or checking_bbox[3] < layer_bbox[0] or checking_bbox[1] > layer_bbox[2]:
                    #not in this layer's bounding box
                    continue
            if options["action"] == "getFeature":
                get_feature_data["feature"] = None
                if isinstance(geometry,Point):
                    if layerdefinition(layer)["geometry_type"] in ["point",'multipoint']:
                        get_feature_data["failed"] = "The {1} layer '{0}' doesn't support action '{2}'. ".format(layer["layerid"],layerdefinition(layer)["geometry_property"]["localType"],options["action"])
                        break
                    else:
                        #polygon or line
                        layer_features = retrieveFeatures(
                            "{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=CONTAINS({},POINT({} {}))".format(kmiserver,layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],geometry.y,geometry.x),
                            session_cookies, layer["layerid"]
                        )["features"]

                else:
                    get_feature_data["failed"] = "Action '{}' Only support Point geometry.".format(options["action"])
                    break
            elif options["action"] == "getIntersectedFeatures":
                get_feature_data["features"] = None
                if isinstance(geometry,Point):
                    if not layer.get("buffer"):
                        get_feature_data["failed"] = "'buffer' is missing in layer '{}'".format(layer["id"])
                        break
                    buff_polygon = Polygon(buffer(geometry.x,geometry.y,layer["buffer"]))
                    layer_features = retrieveFeatures(
                        "{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=INTERSECTS({},POLYGON(({})))".format(kmiserver,layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],"%2C".join(["{} {}".format(coord[0],coord[1]) for coord in list(buff_polygon.exterior.coords)])),
                        session_cookies, layer["layerid"]
                    )["features"]
                elif isinstance(geometry,Polygon):
                    layer_features = retrieveFeatures(
                        "{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&cql_filter=INTERSECTS({},POLYGON(({})))".format(kmiserver,layer["layerid"],layerdefinition(layer)["geometry_property"]["name"],"%2C".join(["{} {}".format(coord[0],coord[1]) for coord in list(geometry.exterior.coords)])),
                        session_cookies, layer["layerid"]
                    )["features"]
                else:
                    get_feature_data["failed"] = "Action '{}' Only support Point and Polygon geometry.".format(options["action"])
                    break

            elif options["action"] == "getClosestFeature":
                get_feature_data["feature"] = None
                layer_feature = None
                if not isinstance(geometry,Point):
                    get_feature_data["failed"] = "Action '{}' Only support Point geometry.".format(options["action"])
                    break
                #should get the grid data at the first try, if can't, set the grid data to null.
                for buff in layer["buffer"] if isinstance(layer["buffer"],(list,tuple)) else [layer["buffer"]]:
                    buff_bbox = Polygon(buffer(geometry.x,geometry.y,buff)).bounds
                    layer_features = retrieveFeatures(
                        "{}/geoserver/wfs?service=wfs&version=2.0&request=GetFeature&typeNames={}&outputFormat=json&bbox={},{},{},{},urn:ogc:def:crs:EPSG:4326".format(kmiserver,layer["layerid"],buff_bbox[1],buff_bbox[0],buff_bbox[3],buff_bbox[2]),
                        session_cookies, layer["layerid"]
                    )["features"]

                    if len(layer_features) == 1:
                        layer_feature = layer_features[0]
                        break
                    elif len(layer_features) > 1:
                        layer_feature = None
                        minDistance = None
                        for feat in layer_features:
                            if layer_feature is None:
                                layer_feature = feat
                                minDistance = getDistance(geometry,shape(feat["geometry"]),p2_proj=layermetadata(layer).get('srs') or "EPSG:4326")
                            else:
                                distance = getDistance(geometry,shape(feat["geometry"]),p2_proj=layermetadata(layer).get('srs') or "EPSG:4326")
                                if minDistance > distance:
                                    minDistance = distance
                                    layer_feature = feat
                        break
                if layer_feature:
                    layer_features = [layer_feature]
            else:
                get_feature_data["failed"] = "Action '{}' Not Support".format(options["action"])
                break

            if layer_features:
                if "feature" in get_feature_data and len(layer_features) > 1:
                    get_feature_data["failed"] = "Found {1} features in layer '{0}' ".format(layer["layerid"],len(layer_features))
                    break
                if layer_features:
                    get_feature_data["id"] = layer["id"]
                    get_feature_data["layer"] = layer["layerid"]
                    for layer_feature in layer_features:
                        feat = {}
                        if layer.get("properties"):
                            for name,column in layer["properties"].items():
                                feat[name] = layer_feature["properties"][column]
                        else:
                            for key,value in layer_feature["properties"].items():
                                feat[key] = value

                        if options.get("format") == "geojson":
                            #return geojson
                            layer_feature["properties"] = feat
                            feat = layer_feature
                        if "feature" in get_feature_data:
                            get_feature_data["feature"] = feat
                        elif "features" in get_feature_data:
                            if get_feature_data["features"]:
                                get_feature_data["features"].append(feat)
                            else:
                                get_feature_data["features"] = [feat]

                    break

    except Exception as error:
        traceback.print_exc()
        get_feature_data["failed"] = "{} from layers ({}) failed.{}".format(options["action"],layers,traceback.format_exception_only(type(error),error))
    return get_feature_data


def spatial(request):
    # needs gdal 1.10+
    try:
        if isinstance(request, SpatialDataCalculation):
            features = json.loads(request.features)
            options = request.options
        else:
            features = json.loads(request.POST.get("features"))
            options = request.POST.get("options")
        if options:
            options = json.loads(options)
        else:
            options = {}

        kmiserver = None
        cookies = settings.SESSION_COOKIE_NAME
        results = []

        features = features["features"] or []
        index = 0
        while index < len(features):
            feature = features[index]
            index += 1
            repairFeatureGeometry(feature)
            feature_result = {}
            results.append(feature_result)
            for key,val in options.items():
                if "action" not in val:
                    val["action"] = key
                if val["action"] == "getArea":
                    feature_result[key] = calculateArea(feature,kmiserver,cookies,val)
                else:
                    feature_result[key] = getFeature(feature,kmiserver,cookies,val)

        #bottle.response.set_header("Content-Type", "application/json")
        #print("{}:return response to client.{}".format(datetime.now(),results))
        output = {"total_features": len(results), "features": results}
        if isinstance(request, SpatialDataCalculation):
            request.output = output
            request.save()
            return
        
        return {"total_features": len(results), "features": results}
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if isinstance(request, SpatialDataCalculation):
            raise e
        # if bottle.response.status < 400 :
        #     bottle.response.status = 400
        #bottle.response.set_header("Content-Type", "text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(exc_type,exc_value)