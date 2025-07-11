from qgis.core import (
    Qgis,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsGeometryValidator,
    QgsLayerTreeGroup,
    QgsMapLayer,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsPoint,
    QgsProject,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import (
    QMetaType,
    QVariant
)
from qgis.PyQt.QtGui import (
    QColor,
    QFont
)
from qgis.utils import iface
from PyQt5.QtCore import QDate
from datetime import date
import uuid

# Functions
#
def messageOut(messageText, title = 'Info', level=Qgis.Info, duration=10):
    """
    Puts message in message bar of QGIS.
    Args:
        title: string for message title (type?)
        messageText: sting with what it is the user should know
        level: QGIS colours the bar accordingly to alert the user. There are four levels Qgis.Info, Qgis.Warning, Qgis.Info and Qgis.Success  Defaults to Qgis.Info
        duration: how long (in seconds) should the message remain in the bar. Set to 0 to make permanent. Defaults to 10s
    Returns:
    """
    mess = iface.messageBar()
    mess.pushMessage(title, messageText, level, duration)
#
def getActive():
    """
    This function checks what the currently active ToC object is. It may not be a layer but a group, which for the purposes of this script is not useful. To expand the utility of this function the return doesn't reject rasters or non-line vectors but returns the information on these objects.
    Args:
        none
    Returns:
        layer or False: if a layer is active in the project side panel (ToC) this is returned. If there are no layers in the project or a group of layers is marked False is returned
    """
    treeView = iface.layerTreeView()
    currentIndex = treeView.selectionModel().currentIndex()
    if not currentIndex.isValid():
        messageOut('Empty project.','Error', Qgis.Critical, 10)
        return False
    node = treeView.index2node(currentIndex)
    if isinstance(node, QgsLayerTreeGroup):
        messageOut('Group of layers marked as active.', 'Error', Qgis.Critical, 10)
        return False
    else:
        layer = iface.activeLayer()
        return layer
#
def layerCheck(layer, feedback = False):
    """
    A health check on the layer that also returns the structure, i.e. raster or vector and which of vector.
    Args:
        layer: the project layer to be checked
        feedback: should the user receive feedback on the layer. Defaults to False
    Returns:
        structure or False: Structure is a string word describing layer. False indicates error with layer
    """
    if layer.isValid() == False:
        if feedback == True:
            messageOut('Invalid layer')
        return False
    if feedback == True:
        messageOut(f'Layer ID: {layer.id()} with crs {layer.crs().userFriendlyIdentifier()}')
    structure = False
    layerStructure = layer.type()
    if layerStructure == QgsMapLayer.RasterLayer:
        structure = 'Raster'
        return structure
    elif layerStructure == QgsMapLayer.VectorLayer:
        structureWordList = ['Unknown', 'NoGeometry', 'Point', 'Line', 'Polygon']
        features = layer.getFeatures()
        feature =QgsFeature()
        features.nextFeature(feature)
        geom = feature.geometry()
        wkb_code = geom.wkbType()
        for word in structureWordList:
            if wkb_code.name.find(word) > -1:
                structure = word
                if feedback == True:
                    messageOut(f'wkbType.name: {wkb_code.name} with {layer.featureCount()} features')
                break
        return structure
    else:
        structure = False
        return structure
#
def getFeatureIterator(layer):
    """
    Uses layer.selectedFeatures() as this returns a list rather than an iterator
    layer.getSelectedFeatures() returns iterator and can be checked with all(False for _ in features) but this will "consume" the first feature
    Args:
        layer: vector layer
    Returns:
        features: An iterator containing the features. Iterators are annoying Python constructions the become even more annoying in PyQGIS
    """
    if len(layer.selectedFeatures()) == 0:
        features = layer.getFeatures()
    else:
        features = layer.getSelectedFeatures()
    return features
#
def createMemoryLayer(structure, crs, fields, name = 'NewLayer'):
        """
        Set up new memory layer. Point, LineString or Polygon. This was fun. Memory layers require LineString. Line creates a layer but QGIS cant find it and there is nothing in it.
        Args:
            structure: vector type
            crs: The coordinate reference system, e.g. layer.crs()
            fields: A list of attribute fields e.g. [QgsField('Attribute1', QMetaType.Type.QString), QgsField('CreationDate', QMetaType.Type.QDate), QgsField('Count', QMetaType.Type.Int), QgsField('Size', QMetaType.Type.Double)]
            name: Text string for layer name in ToC
        Returns:
            vectorLayer: The vector layer for the data
            provider: All that stuff you think should be handled by the layer but isn't because its a feature not a bug. Not that sort of feature.
        """
        crsText = crs.authid()
        uid = str(uuid.uuid4())
        if structure == 'Line':
            structure = 'LineString' 
        uri = f'{structure}?crs={crsText}&uid={uid}'
        vectorLayer = QgsVectorLayer(uri, name, 'memory')
        vectorLayer.setCrs(crs)
        provider = vectorLayer.dataProvider()
        provider.addAttributes(fields)
        vectorLayer.updateFields()
        #messageText = f'Layer created with {uri}, {name}'
        #messageOut(messageText, 'New layer!', Qgis.Info, duration=5)

        return vectorLayer, provider
#
def setLabels(fieldName, size = 8, font = "Arial"):
    """
    Setting labels for newly created layers is wordy. Tried to bundle it all here
    Args:
        fieldName: which field to get labels from
        size: size of text, defaults to 8
        font: label font as string, defaults to Arial
    Returns:
        labelSettings
    """
    labelSettings = QgsPalLayerSettings()
    text_format = QgsTextFormat()
    text_format.setFont(QFont(font, size))
    text_format.setSize(size)
    buffer_settings = QgsTextBufferSettings()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(1)
    buffer_settings.setColor(QColor("white"))
    text_format.setBuffer(buffer_settings)
    labelSettings.setFormat(text_format)
    labelSettings.fieldName = fieldName
    labelSettings.placement =  Qgis.LabelPlacement.AroundPoint
    labelSettings.enabled = True
    labelSettings = QgsVectorLayerSimpleLabeling(labelSettings)

    return labelSettings
#
def addFeature(vectorLayer, provider, newGeometry, newAttributes):
    """
    Convenience for adding new feature to an open vector layer.
    Uses .addFeatures() as this is easier than .addFeature()
    Args:
        vectorLayer: An instantiated vector layer (e.g. QgsVectorLayer(uri, name, 'memory'))
        provider: Whatever these things are (vectorLayer.dataProvider())
        newGeometry: a QgsGeometry object
        newAttributes: a list of attributes in agreement with those defined for the layer
    Returns:
    """
    try:
        newFeature = QgsFeature()
        newFeature.setGeometry(newGeometry)
        newFeature.setAttributes(newAttributes)
        provider.addFeatures([newFeature])
        vectorLayer.commitChanges()
        vectorLayer.updateExtents()
    except:
        message = f'* {newGeometry} with {newAttributes} not added'
        messageOut(message, 'Note')

    return
#
def getVertices(geometry):
    """
    Retrieves vertices from a geometry.
    Args:
        geometry: A QgsGeometry object.
    Returns:
        A list of QgsPointXY objects representing the vertices.
    """
    if geometry.isMultipart():
        parts = []
        for part in geometry.parts():
            if part.isClosed():
                parts.extend(part.asPolygon()[0])
            else:
                parts.extend(part.asPolyline())
        return parts
    elif geometry.wkbType() == QgsWkbTypes.Polygon:
        return geometry.asPolygon()[0]
    elif geometry.wkbType() == QgsWkbTypes.LineString:
        return geometry.asPolyline()
    elif geometry.wkbType() == QgsWkbTypes.Point:
        return [geometry.asPoint()]
    else:
        return []
#
def checkSingleFeatureValidity(feature):
    """
    Runs the PyQGIS built in geometry validator. Perhaps not entirely needed as a separate function.
    Args:
        feature: a QGIS feature object
    Returns:
        errors: a list of errors and their coordinates. for err in errors: print(f'{err.what()} at {err.where()}')
    """
    geom = feature.geometry()
    #valid = geom.isGeosValid()
    #wkb_code = geom.wkbType()
    #wkb_text = QgsWkbTypes.displayString(wkb_code)
    validator = QgsGeometryValidator(geom)
    errors = validator.validateGeometry(geom)
    
    return errors
#
def vertexCheck(layer):
    """
    Overly complex beast of a function the does the bulk of the work.
    Originally only intended to create a dictionary of valid features and produce a point layer of errors if any were found.
    Function expanded after realisation that the point list of vertices for the new polygon is easier to create as the line features are checked for errors.
    This function relies on both the built in geometry validator and a check of line nodes implemented below.
    This checks that each line connects to another at an endpoint and that individual lines do not cross.
    Line order and direction cannot be guaranteed from the user som nothing is assumed here.
    Order is determined by starting from the first line (by fid) and locating a line with a point exactly on its endpoint.
    This is then repeated until each line has been checked
    Args:
        layer: the layer containing the line data. If multiple groups of lines (what will become a polygon) exist then only the first is used due to the code stopping but if a group is selected then that group is used.
    Returns:
        errorCount: integer of number of objects in error point layer
        objectCount: number of line features used
        pointList: a list of PointXY objects in the order defined above
    """
    featureDict = {}
    errorPointLayerLabel = 'Type'
    errorPointLayer,errorPointProvider = createMemoryLayer('Point', layer.crs(), [QgsField(errorPointLayerLabel, QMetaType.Type.QString)], 'Geometry Errors')
    for feature in getFeatureIterator(layer):
        id = feature.id()
        geom = feature.geometry()
        verts = getVertices(geom)
        featureDict[id] = {'feature':feature, 'geom':geom, 'verts':verts} # Number of features (lines) expected to be small (< 100) and memory shouldn't be an issue
    featureIDs = featureDict.keys()
    pointList = []
    for fid in featureIDs:
        # Built in geometry error checker - does not consider hanging lines or crossing features as errors
        errors = checkSingleFeatureValidity(featureDict[fid]['feature'])
        if len(errors) != 0:
            for err in errors:
                addFeature(errorPointLayer,errorPointProvider, QgsGeometry.fromPointXY(err.where()), [f'{err.what()}'])
        currentVerts = featureDict[fid]['verts']
        firstCheck = 'none'
        lastCheck = 'none'
        if len(pointList) == 0:
            for vertex in currentVerts:
                pointList.append(vertex)
        # Loop through features again (gid), hopping over current (fid) feature
        for gid in featureIDs:
            if gid != fid:
                # Does one line feature cross another. This is not caught by built in geometry validator as this is considered valid. This is not the same as self intersect
                if featureDict[gid]['geom'].crosses(featureDict[fid]['geom']):
                    intersect = featureDict[gid]['geom'].intersection(featureDict[fid]['geom'])
                    addFeature(errorPointLayer,errorPointProvider, intersect, ['crossing'])
                # Check if current (fid) line's start point matches either endpoint of gid line
                if (featureDict[gid]['verts'][0] == currentVerts[0]) or (featureDict[gid]['verts'][-1] == currentVerts[0]):
                    firstCheck = 'match'
                # Check if current (fid) line's end point matches either endpoint of gid line
                if (featureDict[gid]['verts'][0] == currentVerts[-1]) or (featureDict[gid]['verts'][-1] == currentVerts[-1]):
                    lastCheck = 'match'
                # Now check if line points are already in list and if they should be appended now. User may have drawn lines in opposite directions.
                if featureDict[gid]['geom'].touches(QgsGeometry.fromPointXY(pointList[-1])):
                    if featureDict[gid]['verts'][0] == pointList[-1]:
                        for vertex in featureDict[gid]['verts']:
                            if vertex not in pointList:
                                pointList.append(vertex)   
                    elif featureDict[gid]['verts'][-1] == pointList[-1]:
                        strev = reversed(featureDict[gid]['verts'])
                        for vertex in strev:
                            if vertex not in pointList:
                                pointList.append(vertex) 
                    else:
                        addFeature(errorPointLayer,errorPointProvider, QgsGeometry.fromPointXY(featureDict[gid]['verts'][0]), ['node order']) # Uncertain how this might come about but can't hurt
        # Check if line group consists of only one line
        objectCount = len(featureDict.keys())
        if objectCount == 1:
            if currentVerts[0] == currentVerts[-1]:
                firstCheck =  lastCheck = 'match'
        if firstCheck == 'none':
            addFeature(errorPointLayer,errorPointProvider, QgsGeometry.fromPointXY(featureDict[fid]['verts'][0]), ['afloat'])
        if lastCheck == 'none':
            addFeature(errorPointLayer,errorPointProvider, QgsGeometry.fromPointXY(featureDict[fid]['verts'][-1]), ['afloat'])
    errorCount = exportErrors(errorPointLayer, errorPointLayerLabel)

    return errorCount, objectCount, pointList
#
def exportErrors(errorPointLayer, errorPointLayerLabel):
    errorCount = 0
    for f in errorPointLayer.getFeatures():
        errorCount = errorCount + 1
    if errorCount >0:
        print(f'Errors: {errorCount}')
        QgsProject.instance().addMapLayer(errorPointLayer)
        labelSettings = setLabels(errorPointLayerLabel, 8)
        errorPointLayer.setLabelsEnabled(True)
        errorPointLayer.setLabeling(labelSettings)
        symbol = QgsMarkerSymbol.createSimple({'name': 'star', 'color': 'red', 'size': 3})
        errorPointLayer.renderer().setSymbol(symbol)
        errorPointLayer.triggerRepaint()
        iface.layerTreeView().refreshLayerSymbology(errorPointLayer.id())
        errorPointLayer.emitStyleChanged()
        errorMessage = f'{errorCount} geometry errors found' 
        messageOut(errorMessage, 'Geometry check', Qgis.Warning, 10)
    else:
        messageOut('No geometry errors found.', 'Geometry check', Qgis.Info, 3)
    
    return errorCount
#
def polygonise():
    layer = getActive()
    if not layer == False:
        structure = layerCheck(layer)
        if structure == 'Line':
            errorCount, objectCount, pointList = vertexCheck(layer)
            if errorCount == 0:
                usedPointLayerLabel = 'Order'
                usedPointLayer, usedPointProvider = createMemoryLayer('Point', layer.crs(), [QgsField(usedPointLayerLabel, QMetaType.Type.Int)], 'Used Points')
                vectorLayer, provider = createMemoryLayer('Polygon', layer.crs(), [QgsField('CreationDate', QMetaType.Type.QDate), QgsField('FromLines', QMetaType.Type.Int)], 'Polygon From Lines')
                plLength = len(pointList)
                plRange = range(plLength)
                print(f'pointList length: {plLength} range: {plRange}')
                for i in plRange:
                    print(f'{i}: {pointList[i]}')
                    pointList[i] = QgsPoint(pointList[i])
                    addFeature(usedPointLayer, usedPointProvider, pointList[i], [i])
                newPolygon = QgsGeometry.fromPolyline(pointList).coerceToType(Qgis.WkbType(3))[0]
                attributes = [QDate(date.today()), objectCount]
                addFeature(vectorLayer, provider, newPolygon, attributes)
                QgsProject.instance().addMapLayer(vectorLayer)
                QgsProject.instance().addMapLayer(usedPointLayer)
                            
                labelSettings = setLabels(usedPointLayerLabel, 8)
                usedPointLayer.setLabelsEnabled(True)
                usedPointLayer.setLabeling(labelSettings)
                symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'black', 'size': 2})
                usedPointLayer.renderer().setSymbol(symbol)
                usedPointLayer.triggerRepaint()
                iface.layerTreeView().refreshLayerSymbology(usedPointLayer.id())
                usedPointLayer.emitStyleChanged()
        else:
            messageOut('Must be line', 'Layer type error!', Qgis.Critical, 10)

if __name__ == "__main__":
    polygonise()
       


        