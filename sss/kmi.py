from django.conf import settings
import traceback
import requests
import sys
import json
from django.core.cache import cache

try:
    import uwsgi
except:
    # ignore uwsgi when profiling
    pass

import xml.etree.ElementTree as ET


def get_child_value(node,child_name):
    try:
        return node.find(child_name).text
    except:
        return None

def layermetadatakey(layerid):
    return "layermetadata_{}".format(layerid)

def layerdefinitionkey(layerid):
    return "layerdefinition_{}".format(layerid)

KB_WORKSPACE_PREFIX = "kaartdijin-boodja"

def is_kb_layer(layerid):
    return bool(layerid) and layerid.strip().startswith(KB_WORKSPACE_PREFIX)

def _normalise_server(url):
    # Callers append "/geoserver/...", so strip any trailing "/geoserver" from the configured base url
    url = (url or "").rstrip("/")
    if url.endswith("/geoserver"):
        url = url[:-len("/geoserver")]
    return url

def get_kmiserver(kmiserver=None, layerid=None):
    """Return the geoserver base url (without '/geoserver') hosting the layer.
    Kaartdijin Boodja layers are served by KB, everything else by KMI."""
    if is_kb_layer(layerid):
        return _normalise_server(settings.KB_API_URL)
    return _normalise_server(settings.KMI_API_URL)

def get_auth(layerid=None):
    if is_kb_layer(layerid):
        return requests.auth.HTTPBasicAuth(settings.KB_AUTH2_BASIC_AUTH_USER,settings.KB_AUTH2_BASIC_AUTH_PASSWORD)
    return requests.auth.HTTPBasicAuth(settings.KMI_AUTH2_BASIC_AUTH_USER,settings.KMI_AUTH2_BASIC_AUTH_PASSWORD)

def get_layermetadata(layerids,kmiserver=None,results={}):
    multiple_layers = True
    if isinstance(layerids,str):
        layerids = [layerids]
        multiple_layers = False
    #group layers against layer workspace
    layers = {}
    for layerid in layerids:
        layerid = layerid.strip()
        #check whether it is cached or not
        key = layermetadatakey(layerid)
        if cache.get(key):
            try:
                metadata = cache.get(key)
                if metadata:
                    if layerid in results:
                        results[layerid].update(json.loads(metadata))
                    else:
                        results[layerid] = json.loads(metadata)
                    #print("Retrieve the metadata from cache for layer ({})".format(layerid))
                    continue
            except:
                pass

        layer = layerid.split(":")

        if len(layer) == 1:
            #no workspace
            layer_ws = ""
            layer = layer[0]
        else:
            layer_ws = layer[0]
            layer = layer[1]

        if layer_ws not in layers:
            layers[layer_ws] = [layer]
        else:
            layers[layer_ws].append(layer)


    if layers:
        session_cookie = settings.SESSION_COOKIE_NAME
        #find the layer's metadata 
        url = None
        requests_by_ws = []
        for layer_ws,ws_layers in layers.items():
            if is_kb_layer(layer_ws):
                # KB workspace capabilities can contain malformed layers, so request each layer's capabilities
                requests_by_ws.extend((layer_ws,[layer],layer) for layer in ws_layers)
            else:
                requests_by_ws.append((layer_ws,ws_layers,None))

        for layer_ws,layers,single_layer in requests_by_ws:
            kmiserver = get_kmiserver(kmiserver,layerid=layer_ws)
            if single_layer:
                url = "{}/geoserver/{}/{}/wms?service=wms&version=1.1.1&request=GetCapabilities".format(kmiserver,layer_ws,single_layer)
            elif layer_ws:
                url = "{}/geoserver/{}/wms?service=wms&version=1.1.1&request=GetCapabilities".format(kmiserver,layer_ws)
            else:
                url = "{}/geoserver/wms?service=wms&version=1.1.1&request=GetCapabilities".format(kmiserver)
            auth_request = get_auth(layer_ws)
            res = requests.get(
                url,
                verify=is_kb_layer(layer_ws),
                auth=auth_request,
                # cookies=session_cookie
            )
            res.raise_for_status()
    
            tree = ET.fromstring(res.content)

            capability = tree.find('Capability')
            if not len(capability):
                raise Exception("getCapability failed")
            kmi_layers = capability.findall("Layer")
            while kmi_layers:
                kmi_layer = kmi_layers.pop()
                name = get_child_value(kmi_layer,"Name")
                
                if name:
                    try:
                        index = layers.index(name)
                    except:
                        index = -1
                    if index >= 0:
                        #this layer's metadata is requsted by the user
                        if layer_ws:
                            layerid = "{}:{}".format(layer_ws,name)
                        else:
                            layerid = name

                        if layerid in results:
                            result = results[layerid]
                        else:
                            result = {"id":layerid}
                            results[layerid] = result

                        del layers[index]
    
                        result["title"] = get_child_value(kmi_layer,"Title")
                        result["abstract"] = get_child_value(kmi_layer,"Abstract")
                        result["srs"] = get_child_value(kmi_layer,"SRS")
                        bbox = kmi_layer.find("LatLonBoundingBox")
                        if bbox is  not None:
                            result["latlonBoundingBox"] = [float(bbox.attrib["miny"]),float(bbox.attrib["minx"]),float(bbox.attrib["maxy"]),float(bbox.attrib["maxx"])]
                        else:
                            result["latlonBoundingBox"] = None
                        for bbox in kmi_layer.findall("BoundingBox"):
                            result["latlonBoundingBox_{}".format(bbox.attrib["SRS"].upper())] = [float(bbox.attrib["miny"]),float(bbox.attrib["minx"]),float(bbox.attrib["maxy"]),float(bbox.attrib["maxx"])]
    
                        #cache it for 6 hours
                        key = layermetadatakey(result["id"])
                        try:
                            if cache.get(key):
                                cache.set(key, json.dumps(result),6 * 3600)
                            else:
                                cache.set(key, json.dumps(result),6 * 3600)
                        except:
                            pass
                            
                        #print("Retrieve the metadata from kmi for layer ({})".format(result["id"]))
    
                        if len(layers):
                            continue
                        else:
                            #already find metadata for all required layers
                            break
                sub_layers = kmi_layer.findall("Layer")
                if sub_layers:
                    kmi_layers += sub_layers
            
            if len(layers) == 1:
                if layer_ws:
                    raise Exception("The layer({}:{}) Not Found".format(layer_ws,layers[0]))
                else:
                    raise Exception("The layer({}) Not Found".format(layers[0]))
            elif len(layers) > 1:
                if layer_ws:
                    raise Exception("The layers({}) Not Found".format(",".join(["{}:{}".format(layer_ws,l) for l in layers])))
                else:
                    raise Exception("The layers({}) Not Found".format(",".join(layers)))

    if multiple_layers:
        return results
    else:
        return results[layerids[0]]

def get_layerdefinition(layerids,kmiserver=None,results={}):
    multiple_layers = True
    if isinstance(layerids,str):
        layerids = [layerids]
        multiple_layers = False
    #group layers against layer workspace
    layers = {}
    for layerid in layerids:
        layerid = layerid.strip()
        #check whether it is cached or not
        key = layerdefinitionkey(layerid)
        if cache.get(key):
            try:
                definitiondata = cache.get(key)
                if definitiondata:
                    if layerid in results:
                        results[layerid].update(json.loads(definitiondata))
                    else:
                        results[layerid] = json.loads(definitiondata)
                    continue
            except:
                pass

        layer = layerid.split(":")

        if len(layer) == 1:
            #no workspace
            layer_ws = ""
            layer = layer[0]
        else:
            layer_ws = layer[0]
            layer = layer[1]

        if layer_ws not in layers:
            layers[layer_ws] = [layerid]
        else:
            layers[layer_ws].append(layerid)

    if layers:
        session_cookie = settings.SESSION_COOKIE_NAME

        url = None
        for layer_ws,layers in layers.items():
            kmiserver = get_kmiserver(kmiserver,layerid=layer_ws)
            if layer_ws:
                url = "{}/geoserver/{}/wfs?request=DescribeFeatureType&version=2.0.0&service=WFS&outputFormat=application%2Fjson&typeName={}".format(kmiserver,layer_ws,",".join(layers))
            else:
                url = "{}/geoserver/wfs?request=DescribeFeatureType&version=2.0.0&service=WFS&outputFormat=application%2Fjson&typeName={}".format(kmiserver,",".join(layers))

            auth_request = get_auth(layer_ws)
            res = requests.get(
                url,
                verify=is_kb_layer(layer_ws),
                auth=auth_request,
                # cookies=session_cookie
            )
            res.raise_for_status()
            layersdata = res.json()

            for layer in layersdata.get("featureTypes") or []:
                if layer_ws:
                    layerid = "{}:{}".format(layer_ws,layer["typeName"])
                else:
                    layerid = layer["typeName"]
                try:
                    index = layers.index(layerid)
                except:
                    index = -1
                if index >= 0:
                    #this layer's metadata is requsted by the user
                    if layerid in results:
                        result = results[layerid]
                    else:
                        result = {"id":layerid}
                        results[layerid] = result

                    result["properties"] = layer["properties"]
                    result["geometry_property"] = None
                    result["geometry_properties"] = []
                    result["geometry_type"] = None
                    result["geometry_property_msg"] = None

                    del layers[index]

                    #find spatial columns
                    for prop in layer["properties"]:
                        if prop["type"].startswith("gml:"):
                            #spatial column
                            result["geometry_properties"].append(prop)


                    if len(result["geometry_properties"]) == 1:
                        result["geometry_property"] = result["geometry_properties"][0]
                        result["geometry_type"] = result["geometry_properties"][0]["localType"].lower()
                    elif len(result["geometry_properties"]) > 1:
                        #have more than one geometry properties, try to find the right one
                        if layer_ws:
                            url = "{}/geoserver/{}/ows?service=WFS&version=2.0.0&request=GetFeature&typeName={}&count=1&outputFormat=application%2Fjson".format(kmiserver,layer_ws,layerid)
                        else:
                            url = "{}/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName={}&count=1&outputFormat=application%2Fjson".format(kmiserver,layerid)
                        auth_request = get_auth(layer_ws)
                        res = requests.get(
                            url,
                            verify=is_kb_layer(layer_ws),
                            #cookies=session_cookie
                            auth=auth_request
                        )
                        res.raise_for_status()
                        featuresdata = res.json()
                        if len(featuresdata["features"]) > 0:
                            feat = featuresdata["features"][0]
                            for prop in result["geometry_properties"]:
                                if prop["name"] == feat["geometry_name"]:
                                    result["geometry_property"] = prop
                                    result["geometry_type"] = prop["localType"].lower()
                                    break

                        if not result["geometry_property"]:
                            result["geometry_property_msg"] = "Layer '{}' has more than one geometry columns, can't identity which column is used as the geometry column.".format(layerid)
                    else:
                        result["geometry_property_msg"] = "Layer '{}' is not a spatial layer".format(layerid)

                    if result["geometry_property"]:
                        #found the geometry property, remove it from properties
                        index = len(result["properties"]) - 1
                        while index >= 0:
                            if result["properties"][index] == result["geometry_property"]:
                                #this is the geometry property,remove it from properties
                                del result["properties"][index]
                                break
                            index -= 1



                    #cache it for 1 day
                    key = layerdefinitionkey(layerid)
                    try:
                        if uwsgi.cache_exists(key):
                            uwsgi.cache_update(key, json.dumps(result),24 * 3600)
                        else:
                            uwsgi.cache_set(key, json.dumps(result),24 * 3600)
                    except:
                        pass
                        
        if len(layers) == 1:
            if layer_ws:
                raise Exception("The layer({}:{}) Not Found".format(layer_ws,layers[0]))
            else:
                raise Exception("The layer({}) Not Found".format(layers[0]))
        elif len(layers) > 1:
            if layer_ws:
                raise Exception("The layers({}) Not Found".format(",".join(["{}:{}".format(layer_ws,l) for l in layers])))
            else:
                raise Exception("The layers({}) Not Found".format(",".join(layers)))

    if multiple_layers:
        return results
    else:
        return results[layerids[0]]

def layermetadata():
    try:
        kmiserver = request.GET.get("server") 
        kmiserver = get_kmiserver(kmiserver)
        
        layers = request.GET.get("layers")
        if not layers:
            raise Exception("Missing parameter 'layers'")
        else:
            layers = [l.strip() for l in layers.split(",") if l.strip()]

        #bottle.response.set_header("Content-Type", "application/json")
        results = get_layermetadata(layers,kmiserver)
        results = get_layerdefinition(layers,kmiserver,results=results)
        if len(layers) == 1:
            return results[layers[0]]
        else:
            return results
    except:
        #if bottle.response.status < 400 :
        #    bottle.response.status = 400
        #bottle.response.set_header("Content-Type","text/plain")
        traceback.print_exc()
        return traceback.format_exception_only(sys.exc_type,sys.exc_value)
    