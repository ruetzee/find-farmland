
# coding: utf-8

# In[11]:


import xml.etree.cElementTree as ET
import fiona
from fiona.crs import from_epsg
from shapely.geometry import Polygon, mapping

import sys
from copy import deepcopy

import time

#generalization constants
#  FILE = 'tunisia.osm'
FILE = sys.argv[1]
USE_LIST = ["farmyard","farmland","farm"]
DRIVER = 'ESRI Shapefile'
EPSG_CODE = 4326
OUTPUT_FILE = sys.argv[2]
BATCH_SIZE = 100
#  OUTPUT_FILE = "test1.shp"

def writeToShapefile(wayDic, fileMode):
    # (wayID, way name) => [(lon, lat), (lon, lat), ...]
    lonLatDict = {way:[None]*len(wayDic[way]) for way in wayDic}

    # populate a new dictionary with way -> long-lat information
    count = 0
    l = len(wayDic)
    for way in wayDic:
        if count % 1000 == 0:
            print('Way {} of {}'.format(count, l))
        for i in range(len(wayDic[way])):
            lonLatDict[way][i] = nodeDict[wayDic[way][i]]
        count += 1

    #  create polygons from the dictionary and output them to a .shp file
    schema = {'geometry': 'Polygon', 'properties': {'Name':'str:80'}}
    shapeout = OUTPUT_FILE
    with fiona.open(shapeout,fileMode,crs=from_epsg(EPSG_CODE),driver=DRIVER, schema=schema) as output:
        for way in lonLatDict:
            # Hack to avoid LinearRing error?? (Some "polygons" only have two
            # vertices for some reason.......)
            if len(lonLatDict[way]) > 2:
                poly = Polygon(lonLatDict[way])
				#name = blah blah
                output.write({'geometry': mapping(poly), 'properties': {'Name':name}})
                
#get time before parsing tree, define dictionaries
t1 = time.time()
wayDict = {} # (way ID, way name) => [node references]
nodeDict = {} # (node ID) => (lon, lat)


tree = ET.iterparse(FILE)
i = 0
mode = 'w'
for event, elem in tree:
    if event == 'end':
        #if it's a node, store only its id and lat-long info
        if elem.tag == 'node':
            nodeDict[elem.attrib['id']] = \
                    (float(elem.attrib['lon']), float(elem.attrib['lat']))
            elem.clear()
        #if it's a landuse way of interest, store it in wayDict
        elif elem.tag == 'way':
            add = False
            name = ''
            tags = elem.findall('tag')
            for tag in tags:
                if 'k' in tag.attrib:
                    if tag.attrib['k'] == "landuse":
                        if tag.attrib['v'] in USE_LIST:
                            add = True
                    elif tag.attrib['k'] == 'name':
                        name = tag.attrib['v']
            if add:
                wayDict[(elem.attrib['id'], name)] = \
                        [nd.attrib['ref'] for nd in elem.findall('nd')]
            elem.clear()

    if i % BATCH_SIZE == 0 and i != 0:
        print('Processing batch up to element {}'.format(i))
        if i > BATCH_SIZE and mode != 'a':
            mode = 'a'
        writeToShapefile(wayDict, mode)
        wayDict = {}
    i += 1
if len(wayDict) != 0:
    writeToShapefile(wayDict, mode)
    wayDict = {}



#get time after parsing and before dictionary building, calculate and print how long it took
#t2 = time.time()
#parsetime = t2-t1
#print('finished parsing tree, took {:.2f} seconds'.format(parsetime))



#get time after dictionary building, calculate and print how long it took
#t3 = time.time()
#lonlattime = t3-t2
#print('finished latlon, took {:.2f} seconds'.format(lonlattime))



#    t4 = time.time()
#    alltime = t4-t1
#    print('finished writing, whole process took {:.2f} seconds'.format(alltime))
