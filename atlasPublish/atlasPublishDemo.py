#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jame6423
#
# Created:     03/02/2015
# Copyright:   (c) jame6423 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, json, os, urllib2, urllib
#For editing the service configuration
import xml.dom.minidom as DOM

#globals
blankMXD = r'D:\Demos\FedUC\FEDUC_2015\demos\atlas\tools\blank.mxd'
default_connection = r'D:\Demos\FedUC\FEDUC_2015\demos\atlas\tools\connection.ags'
webMerc = arcpy.SpatialReference(3857)

def msg(inMsg):
    text = '{0}'.format(inMsg)
    print(text)
    arcpy.AddMessage(text)

def makeLayerMap(layer, outDir):
    #Copy the Layer to a new, blank map
    layer.visible = True
    newMap = arcpy.mapping.MapDocument(blankMXD)
    df0 = arcpy.mapping.ListDataFrames(newMap)[0]
    arcpy.mapping.AddLayer(df0, layer)
    df0.spatialReference = webMerc

    #Check for spaces in layer name
    layerName = layer.name
    if layerName.find(' ') >= 0:
        layerName = layer.name.replace(' ', '')


    #Set Tags and Summary to remove warnings
    newMap.tags = ','.join([layer.name, 'atlas'])
    newMap.summary = layer.name.title() + ' layer for an atlas'
    #Save a copy- possibly for reference
    msg(layerName)
    msg(os.path.join(outDir, layerName + '.mxd'))
    newMap.saveACopy(os.path.join(outDir, layerName + '.mxd'))
    return layerName

def makeSDFile(inName, outDir, replace, cache, serverConnection=default_connection, serverFolder="Atlas"):
    #Load the map for publishing
    outMap = arcpy.mapping.MapDocument(os.path.join(outDir, inName + '.mxd'))
    msg("\t-Service Defintion Draft")
    sdDraftFile = os.path.join(outDir, inName + '.sddraft')
    newSDdraft = arcpy.mapping.CreateMapSDDraft(
        map_document = outMap,
        out_sddraft = sdDraftFile,
        service_name = inName,
        server_type = 'ARCGIS_SERVER',
        connection_file_path = serverConnection,
        copy_data_to_server = True,
        folder_name = serverFolder
    )

    #Modifications
    #Derived from the samples in the function's documentation,
    # http://desktop.arcgis.com/en/desktop/latest/analyze/arcpy-mapping/createmapsddraft.htm
    if replace or cache:
        doc = DOM.parse(sdDraftFile)
        if replace:
            #modify the SDDraft to overwrite existing service
            newType = 'esriServiceDefinitionType_Replacement'
            descriptions = doc.getElementsByTagName('Type')
            for desc in descriptions:
                if desc.parentNode.tagName == 'SVCManifest':
                    if desc.hasChildNodes():
                        desc.firstChild.data = newType
        if cache:
            # turn on caching in the configuration properties
            configProps = doc.getElementsByTagName('ConfigurationProperties')[0]
            propArray = configProps.firstChild
            propSets = propArray.childNodes
            for propSet in propSets:
                keyValues = propSet.childNodes
                for keyValue in keyValues:
                    if keyValue.tagName == 'Key':
                        if keyValue.firstChild.data == "isCached":
                            # turn on caching
                            keyValue.nextSibling.firstChild.data = "true"
        f = open(sdDraftFile, 'w')
        doc.writexml(f)
        f.close()
    return sdDraftFile


def publishSDFile(sdDraftFile, layerName, cache, connectionFile=default_connection, serverFolder = 'Atlas'):
    sdFile = sdDraftFile.replace('draft', '')
    msg("\t-Service Defintion Stage")
    arcpy.StageService_server(sdDraftFile, sdFile)
    msg("\t-Service Defintion Upload")
    arcpy.UploadServiceDefinition_server(sdFile, connectionFile)

    #Start caching
    if cache:
        msg("\t-Caching Service")
        arcpy.ManageMapServerCacheTiles_server(connectionFile[:-4] + "//" + serverFolder + "//" + layerName + ".MapServer","18489297.737236;9244648.868618;4622324.434309;2311162.217155;1155581.108577;577790.554289;288895.277144","RECREATE_ALL_TILES","3","Feature Set",wait_for_job_completion = "DO_NOT_WAIT")

    #record the service location
    return '//{0}//{1}//{2}/MapServer'.format(connectionFile[:-4], serverFolder, layerName)

def main():
    inMXD = r'D:\Demos\FedUC\FEDUC_2015\demos\atlas\atlas-master.mxd'
    outDir = r'D:\Demos\FedUC\FEDUC_2015\demos\atlas\Atlas'
    replace = True
    cache = True
    scales = "288895.277144;144447.638572;72223.819286;36111.909643"
    # inMXD = arcpy.GetParameterAsText(0)
    # outDir = arcpy.GetParameterAsText(1)
    # replace = arcpy.GetParameter(2)
    # cache = arcpy.GetParameter(3)

    sourceMap = arcpy.mapping.MapDocument(inMXD)
    outServices = []
    for layer in arcpy.mapping.ListLayers(sourceMap):
        if layer.longName.find('SKIP') == -1:
            if layer.isGroupLayer:
                pass
            else:
                try:
                    msg(layer.name)
                    layerName = makeLayerMap(layer, outDir)
                    layerSDFile = makeSDFile(layerName, outDir, replace, cache)
                    outService = publishSDFile(layerSDFile, layerName, cache)
                    outServices.append(outService)
                    msg('---------------------')
                except Exception as e:
                    msg('Error')
                    msg(e.args)
                    msg(e.message)
    msg('\n'.join(outServices))


