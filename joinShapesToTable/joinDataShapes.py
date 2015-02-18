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

import arcpy, random, os

def msg(inMsg):
    text = '{0}'.format(inMsg)
    print(text)
    arcpy.AddMessage(text)

def getRows(inTable, fields, indexfield, shapeWhereClause):
    outRows = None
    try:
        outRows = {}
        if indexfield:
            indexPosition = fields.index(indexfield)
        #Describe existing shapes to get shape type and spatial reference
        msg('reading in shapes')
        #Load the existing shapes
        i = 0
        with arcpy.da.SearchCursor(inTable, fields, shapeWhereClause) as cur:
            for row in cur:
                if indexfield:
                    if row[indexPosition] in outRows:
                        raise ValueError('duplicate join value')
                    outRows[row[indexPosition]] = row
                else:
                    outRows[i] = row
                    i = i + 1
        return outRows
    except ValueError as e:
        arcpy.AddError("Invalid value: " + e )
    except Exception as e:
        msg(e.args)
        msg(e.message)
        msg('Error')

def createTempFC(shapeType, inTable, sr):
    #get a name with little chance of overwrite
    FCname = "temp_" + str(int(random.random()*1000))
    #the FC has the shape type of inShapes and schema of inTable
    msg('Creating temporary Feature Class')
    tempFC = arcpy.CreateFeatureclass_management("in_memory", FCname, shapeType, spatial_reference = sr)

    #Add Fields
    desc = arcpy.Describe(inTable)
    for field in desc.fields:
        if field.type != 'OID':
            arcpy.AddField_management(tempFC, field.name, field.type, field_length = field.length )

    return tempFC

def getFields(inTable, skipOID=True, skipGeometry=True):
    fieldList = []

    #Use Describe to get to field names
    desc = arcpy.Describe(inTable)
    fields = desc.fields
    for field in fields:
        #Are we keeping OID or geometry fields?  No, then skip
        if field.type == 'OID' and skipOID:
            pass
        elif field.type == 'Geometry' and skipGeometry:
            pass
        else:
            fieldList.append(field.name)
    return fieldList


def shapeToTable(inTable, tableJoinField, inShapes, shapesJoinField, shapeWhereClause, outfc):
    try:
        desc = arcpy.Describe(inShapes)
        if not desc.shapeType.upper() in ["POINT", "MULTIPOINT", "POLYGON", "POLYLINE"]:
            raise ValueError("Shape Type is invalid")

        #Get the shapes indexed by the join field values
        outShapes = getRows(inShapes, [shapesJoinField, 'SHAPE@'], shapesJoinField, shapeWhereClause)

        #Create a temporary feature class for processing
        tempFC = createTempFC(desc.shapeType.upper(), inTable, desc.spatialReference)
        tableFieldNames = getFields(inTable)

        #Identify the index of the join field in the table for use in lookup
        msg('join table')
        joinPosition = tableFieldNames.index(tableJoinField)

        #Get the table Rows
        tableRows = getRows(inTable, tableFieldNames, None, None)

        outRows = []
        #Join the shapes and table rows together
        for i, row in tableRows.iteritems():
            #The rows are tuples, so we need to create a new outRow list
            #Reminder - the shape field list was keyfield, SHAPE@
            #We only need SHAPE@ since the key value is coming with the table
            shapeKey = row[joinPosition]
            outShape = outShapes[shapeKey][1]
            outRow = [outShape]
            outRow.extend(row)
            outRows.append(outRow)

        #Create an insert cursor on the temporary FC and insert the rows
        msg('load and join table')
        outFields = ['SHAPE@']
        outFields.extend(tableFieldNames)

        with arcpy.da.InsertCursor(tempFC, outFields) as insert:
            for oRow in outRows:
                insert.insertRow(oRow)

        msg('Copying to output')
        #Copy out to the FC
        outCopy = arcpy.CopyFeatures_management(tempFC, outfc).getOutput(0)
        return outCopy

    except ValueError as e:
        arcpy.AddError("Invalid value: " + e )
    except Exception as e:
        msg(e.args)
        msg(e.message)
        msg('Error')

    finally:
        #Clean up the temporary file
        arcpy.Delete_management(tempFC)


def main():
    inTable = arcpy.GetParameterAsText(0)
    tableJoinField = arcpy.GetParameterAsText(1)
    inShapes = arcpy.GetParameterAsText(2)
    shapesJoinField = arcpy.GetParameterAsText(3)
    shapeWhereClause = arcpy.GetParameterAsText(4)
    outfc = arcpy.GetParameterAsText(5)

    out = shapeToTable(inTable, tableJoinField, inShapes, shapesJoinField, shapeWhereClause, outfc)
    arcpy.SetParameter(5, outfc)
    pass

if __name__ == '__main__':
    main()
