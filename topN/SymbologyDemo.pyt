import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Symbology Demonstration"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Highlight Top N Features"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        #Input Layer
        param0 = arcpy.Parameter(
            displayName="Layer",
            name="in_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polygon"]

        #Field to symbolize
        param1 = arcpy.Parameter(
            displayName="Symbolization Field",
            name="field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        param1.filter.list = ['Short', 'Long', 'Single', 'Double']
        param1.parameterDependencies = [param0.name]

        #Number to Highlight
        param2 = arcpy.Parameter(
            displayName="Number to Highlight",
            name="topNum",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        param2.value = 5

        #Output layer, if used in model
        param3 = arcpy.Parameter(
            displayName = 'Output Layer',
            name = 'out_layer',
            datatype="GPFeatureLayer",
            parameterType='Derived',
            direction='Output'
        )
        param3.parameterDependencies = [param0.name]
        param3.schema.clone = True

        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        layerName = parameters[0].valueAsText
        field = parameters[1].valueAsText
        topNum = parameters[2].value

        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        lyr = arcpy.mapping.ListLayers(mxd, layerName)[0]
        breaks = self.calculateBreaks(lyr.dataSource, field, topNum, lyr.definitionQuery)
        self.updateLayer(df, lyr, field, breaks)
        return

    def calculateBreaks(self, inFC, field, topNum, defQuery=None):
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

    def updateLayer(self, df, lyr, field, breaks):
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
        return
