#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jame6423
#
# Created:     02/02/2015
# Copyright:   (c) jame6423 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy

def calculateBreak(inFC, field, topNum, defQuery=None):
    #Create variables to store the output (breaks) and a list of all values
    outbreak = []
    featureValues = []

    #Load the feature values into the list
    with arcpy.da.SearchCursor(inFC, [field], defQuery) as cursor:
        for row in cursor:
            featureValues.append(row[0])

    #Sort the values smallest to largest
    featureValues.sort(reverse=True)

    #When setting breaks with arcpy.mapping, we set the minimum AND maximum value of a class
    #Therefore, we need 3 values:
    #The minimum value of the set (last after sort)
    #The Nth-1 item's value, which is featureValues[N]
    #The max value featureValues[0]
    topBreak = featureValues[topNum]

    outbreaks = [float(featureValues[-1]), float(topBreak), float(featureValues[0])]
    return outbreaks

def updateLayer(df, lyr, field, breaks):
    #Update the symbology to the templates.  This gives us a graduated color based on
    #a gray to yellow ramp
    templateLayerPath = "./topN.lyr"
    templateLayer = arcpy.mapping.Layer(templateLayerPath)
    arcpy.mapping.UpdateLayer(df, lyr, templateLayer)

    #We know the template uses graduated colors, but should still test as a best practice
    if lyr.symbologyType == "GRADUATED_COLORS":
        #Update the field and breaks of the symbology
        symbology = lyr.symbology
        symbology.valueField = field
        symbology.classBreakValues = breaks

def main():
    layerName = arcpy.GetParameterAsText(0)
    field = arcpy.GetParameterAsText(1)
    topNum = int(arcpy.GetParameterAsText(2))

    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    lyr = arcpy.mapping.ListLayers(mxd, layerName)[0]
    if lyr.supports ('dataSource'):
        breaks = calculateBreak(lyr.dataSource, field, topNum, lyr.definitionQuery)
        updateLayer(df, lyr, field, breaks)
    pass

if __name__ == '__main__':
    main()
