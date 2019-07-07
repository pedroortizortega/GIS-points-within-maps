"""
@author: Pedro Ortiz
"""
# -*- coding: utf-8 -*-
import json
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Point
import requests
import re
import glob
#---------------------------------------------------------------------------------
# Credentials
AppID = r'API_ID_HERE'
AppCode = r'API_CODE_HERE'
#--------------------------------------------------------------------------------
#- Fuinction to take the points inside a polygon
def SpatialJoin(dataframe1, Geodataframe2):
  """A spatial join function where each data frame don't need  index in their columns """
  dataframe1['Geometry']= list(zip(dataframe1.long, dataframe1.lat))
  dataframe1['Geometry'] = dataframe1['Geometry'].apply(Point)
  Geodataframe1 = gpd.GeoDataFrame(dataframe1, geometry = 'Geometry')
  # Note = The crs have to be the same crs as the opportunity zone, Setting up the two geodataframe with the same crs
  Geodataframe1.crs = Geodataframe2.crs
  # Now, we have the same crs, so we can make a spatial join between geodataframes
  # Making a spatial join between the polygon and the random points
  # using the attribute 'within' we join only the points 
  # that have the coordinates within the polygon (opp zone)
  join = gpd.sjoin(Geodataframe1, Geodataframe2 ,  how="inner", op='within')
  return join
#--------------------------------------------------------------------------------
#- Creating the array of cluster points
def initialDocsForCenter(shapeFileState, dataFramePath, city, rename=False):
  # Reading the data files from the Census webpage
  interestedPolygon = gpd.read_file(shapeFileState)
  if ".xlsx" in dataFramePath:
    Points = pd.read_excel(dataFramePath).set_index("NAME")
  else:
    Points = pd.read_csv(dataFramePath).set_index("NAME")
  if rename:
    Points = Points.rename(index=str, columns={"LAT": "lat", "LON": "long"})
  else:
    print("No renamed file")  
  centroidInterestedZone = interestedPolygon.centroid
  return interestedPolygon, Points, centroidInterestedZone
#--------------------------------------------------------------------------------
#- cluster Machine Learning code
def clusterMachineLearning(dataFrame, numberOfClusters):
    from sklearn.cluster import KMeans
    # create kmeans object
    kmeans = KMeans(n_clusters=numberOfClusters,init ='random',  n_init=300)
    # fit kmeans object to data
    kmeans.fit(dataFrame)
    # print location of clusters learned by kmeans object
    print(kmeans.cluster_centers_)
    clustersInterested = kmeans.cluster_centers_
    # save new clusters for chart
    dataFrame["Zone"] = kmeans.labels_
    print("len DF= ", len(dataFrame))
    return clustersInterested, dataFrame
#----------------------------------------------------------------------------------
#- Calling the HERE API to get the coordinates to the Time Zones
def hereMinerTimeZone(timeRadius, point):
    #-- making the query--------
    point = '{},{}'.format(point[0], point[1])
    url = r"https://isoline.route.api.here.com/routing/7.2/calculateisoline.json?"
    params = {
              'start' : point,
              'range' : str(timeRadius),
              'rangetype' : 'time',
              'mode' : 'fastest;car;traffic:enabled',
              'app_id' : AppID,
              'app_code' : AppCode
             }
    r = requests.get(url=url, params=params)
    r = r.text.replace('\0', '')
    r = json.loads(r)
    jsonn = r
    return jsonn
#-------------------------------------------------------------------------------
#--> Calling the HERE API to get the travel time betwenn two points
def hereMinerTimeBetween2Points(centroid, point):
    #-- making the query--------
    centroid = '{},{}'.format(centroid[0], centroid[1])
    pointInterested = '{},{}'.format(point[0], point[1])
    url = r"https://route.api.here.com/routing/7.2/calculateroute.json?"
    params = {
              'waypoint0' : centroid,
              'waypoint1' : pointInterested,
              'mode' : 'fastest;car;traffic:enabled',
              'app_id' : AppID,
              'app_code' : AppCode,
              'departure' : 'now'
             }
    r = requests.get(url=url, params=params)
    r = r.text.replace('\0', '')
    r = json.loads(r)
    jsonn = r
    return jsonn
#-------------------------------------------------------------------------------
#--> Translating the json file into a dictionary
def travelPointsFrom2Waypoints(polygon, centroid, interestedPoints, exitTravelPointsName):
  clustersPointsJSON = []
  travelTimePoints = {}
  for rows in interestedPoints.iterrows():
    columns = rows[1]
    index = rows[0]
    interestedPoint = [columns.lat , columns.long]
    jsonn = hereMinerTimeBetween2Points(centroid, interestedPoint )
    clustersPointsJSON.append(jsonn)
    #--> Up to here, you created a list with the interested points
    #  for point in clustersPointsJSON:
    if "response" in jsonn.keys():
      response = jsonn['response']['route'][0]['summary']
      distanceBetween2Points = response["distance"]
      travelTimeBetween2Points = response["travelTime"]
      travelTimePoints[index] = {
      "Travel time": travelTimeBetween2Points,
      "Distance " : distanceBetween2Points,
      "lat" : columns.lat,
      "long" : columns.long,
      "Phone" : columns.PHONE
      }
    else:
      print("No geocoder")              
      travelTimePoints[index] = {
      "Travel time": np.nan,
      "Distance " : np.nan,
      "lat" : columns.lat,
      "long" : columns.long,
      "Phone" : columns.PHONE
      } 
  dfPoints = pd.DataFrame.from_dict(travelTimePoints, orient='index')
  exitTravelPointsNameCSV = "{}.csv".format(exitTravelPointsName)
  dfPoints.to_csv(exitTravelPointsNameCSV)
  return dfPoints
#-------------------------------------------------------------------------------
#- Making a dfta frame from array
def makingDataFrameFromArray(clustersArray, city, county, state, Print=False):
  data = {}
  lats = []
  longs = []
  for counter in range(len(clustersArray)):
    x = clustersArray[counter]
    lats.append(x[0])
    longs.append(x[1])      
  data["lat"] = lats
  data["long"] = longs
  centroids = pd.DataFrame.from_dict(data)
  centroids["City"] = city
  centroids["County"] = county
  centroids["State"] = state
  if Print:
    centroids.to_csv("centroids{}_{}.csv".format(city, state))
  else:
    print("No printed")
  return centroids
#-------------------------------------------------------------------------------
#--> Making the Points in the difference Set operation between geodataframes
def makingZonePoints(listNumberofZone, listDifferenceZones, folderExit= r"C:\Users\user\Documents\Projects\Geo-distribution\GIS", nameFileExit= r"PointsTimeZone", pathPointsFileExcel= r"data-file.xlsx"):
  """
  In order to use this function, put all together the shape files from the zones that you was created.
  This fuunction has the option to put the nameFileExit, the the path for the excel file of the Points
  and the path of the exit folder where the new files going to be alocated.

  listDifferenceZones= ["2700_2400", "2400_1800", "2100_1800", "1800_1500","1500_1200", "1200_900", "900_600", "600_300" ]
  listNumberofZone = [0,1,2,3,4,5,6]

  It is mandatory put the list of the difference zones as NumberOfZoneB_NumberOfZoneA where the difference in set operation is B - A
  """
  lisDF = []
  for zone in listNumberofZone:
    for zones in listDifferenceZones:
        zones = re.findall(r"\d+", zones)
        B =zones[0]
        A = zones[1]
        fileName=nameFileExit
        zone_B = gpd.read_file(r"polygon_{}_{}_s{}.shp".format(fileName, zone, B))
        zone_A = gpd.read_file(r"polygon_{}_{}_s{}.shp".format(fileName, zone, A))
        Points = pd.read_excel(pathPointsFileExcel)
        nameExit=r"{}{}_{}_{}".format(nameFileExit, zone, B, A)
        gdf = differenceGeoSpatialPoints(zone_B, zone_A, Points, zone, A, B, Print=True,  folderExit=folderExit, nameExit=nameExit, date= r"19022019")
        lisDF.append(pd.DataFrame(gdf))
  dfAll=pd.concat(lisDF, axis=0, join='outer')  
  return dfAll
#-------------------------------------------------------------------------------
#- Making a difference Set operation between geodataframes
def differenceGeoSpatialPoints(Zone1, Zone2, Points, zone, A , B, Print=False, folderExit=".", nameExit="differencePoints", date="2019"):
  differenceZone1MinusZone2 = gpd.overlay(Zone1, Zone2, how='difference')
  pointsDifferenceZones = SpatialJoin(Points, differenceZone1MinusZone2)
  if Print:
    pathExit = r"{}\{}_{}.csv".format(folderExit, nameExit, date)
    dfOut = pd.DataFrame(pointsDifferenceZones)
    dfOut["Zone"] = zone
    dfOut["Time"] = int(B)
    dfOut.to_csv(pathExit)
    pointsDifferenceZones = dfOut
  else:
    print("No CSV printed")
  return pointsDifferenceZones
#-------------------------------------------------------------------------------
#--> Preparing the dato to the Machine Learning process
def preperingDataFrameToML(dfOut, DFwithOutIndexName=False):
  #- Preparing the files to
  dfOut = dfOut.dropna()
  if DFwithOutIndexName:
    dfOut = dfOut[dfOut.Zone.notna()].set_index("NAME")
  else:
    print("No necesary index")
  columnsName = input("If you have KeyError, try this(y) ==>")
  if columnsName == "y":
    lat = input("What is the name for the Latitude column? ==> ")
    long = input("What is the name of the Longitud column? ==>")
    Distance = input("What is the name of the Distance column? ==>")
    Travel = input("What is the name of the travel time column? ==>") 
    dfOut = dfOut[[
            lat, 
            long, 
            Distance, 
            Travel
            ]]
  else:  
    dfOut = dfOut[[
              "lat", 
              "long", 
              "Travel time 0",
              "Travel time 1",
              "Travel time 2",
              "Travel time 3",
              "Travel time 4",
              "Travel time 5",
              "Travel time 6"
              ]]
  return dfOut
#-------------------------------------------------------------------------------
#- Making a difference Set operation between geodataframes
def preparingFilesToML(folderInitialFiles, patern, typeOfFiles="csv"):
  listFile = []
  for filename in glob.iglob(r'{}\{}.{}'.format(folderInitialFiles, patern, typeOfFiles), recursive=True):
      df = pd.read_csv(filename)
      listFile.append(df)
  dfOut = pd.concat(listFile, axis=0, join='outer')
  #----------------------------------------------------------
  #- Preparing the files to 
  dfOut = preperingDataFrameToML(dfOut)
  return dfOut
#-------------------------------------------------------------------------------
def mergingTwoPolygonsByCities(shapeFilePath, isPolygonAvaible=False):
  listPolygons = []
  if isPolygonAvaible:
    shapeFile = shapeFilePath
  else:
    shapeFile = gpd.read_file(shapeFilePath)
  HowManys = input("How many polygons do you want? ==>")
  contador = 1
  while contador < int(HowManys):
    if contador == 1:    
      city1 = input("Which is your {} city? ==>".format(contador))
      #-- Polygon 1
      interestedPolygon1 = shapeFile[shapeFile.NAME10.str.contains(city1)]
      print("----------------City ------------------------------")
      print(interestedPolygon1.head(20))
      column1 = input("Which column name? ==> ")
      row1 = input("Which row name? ==> ")
      print("----------------------------------------------------")      
      interestedPolygon1 = interestedPolygon1[interestedPolygon1[column1] == row1]
      listPolygons.append(interestedPolygon1)    
      #-- Polygon 2
      print("----------------City 2------------------------------")
      city2 = input("Which is your {} city? ==>".format(contador+1))
      interestedPolygon2 = shapeFile[shapeFile.NAME10.str.contains(city2)]
      print(interestedPolygon2.head(20))
      column2 = input("Which column name? ==> ")
      row2 = input("Which row name? ==> ")
      interestedPolygon2 = interestedPolygon2[interestedPolygon2[column2] == row2]
      print("----------------------------------------------------")
      unionZone1WithZone2 = gpd.overlay(interestedPolygon1, interestedPolygon2, how='union')
      Print = input("Do you want to write the SHAPEFILE? Write y for yes ==> ")
      if Print == "y":
          fileNameExit = input("What is the name for the new shape file? ==> ")
          unionZone1WithZone2.to_file(filename='{}.shp'.format(fileNameExit), driver="ESRI Shapefile")
          print("Writed")
      else:
          print("no writed")
    #-- Merging two polygons
    elif contador >= 2:
      print("----------------City other------------------------------")
      city2 = input("Which is your {} city? =".format(contador+1))
      interestedPolygon2 = shapeFile[shapeFile.NAME10.str.contains(city2)]
      print(interestedPolygon2.head(20))
      column2 = input("Which column name? ==> ")
      row2 = input("Which row name? ==> ")
      interestedPolygon2 = interestedPolygon2[interestedPolygon2[column2] == row2]
      print("----------------------------------------------------")
      unionZone1WithZone2 = gpd.overlay(unionZone1WithZone2, interestedPolygon2, how='union')
      Print = input("Do you want to write the SHAPEFILE? Write y for yes ==> ")
      if Print == "y":
          fileNameExit = input("What is the name for the new shape file? ==> ")
          unionZone1WithZone2.to_file(filename='{}.shp'.format(fileNameExit), driver="ESRI Shapefile")
          print("Writed")
      else:
          print("no writed")
    contador = contador + 1
  return unionZone1WithZone2
#-------------------------------------------------------------------------------
#- With this funciton you can get the points which are inside in any polygon
def pointsWithinPolygon(dataFramePath, polygon, exitName):
  #-- reading the data frame with points
  if ".xlsx" in dataFramePath:
    Points = pd.read_excel(dataFramePath)
  elif ".csv" in dataFramePath:
    Points = pd.read_csv(dataFramePath)
  else:
    Points = dataFramePath
  #------------------------------------
  #--> 
  if ".shp" in  polygon:
    geoPolygon = gpd.read_file(polygon)
  else:
    geoPolygon = polygon
  geoPolygon = geoPolygon[geoPolygon.geometry.notna()]
  isCity = input("Do you want to specify some polygon within the shape file (y) or just a UNARY UNION(u)?==> ")
  if "y" in str(isCity).lower():
    print(geoPolygon.head()) 
    ct = input("Which city?==> ")
    col = input("Which column?==> ")
    geoPolygon = geoPolygon[geoPolygon[col].map(str).str.contains(ct)]
    print(geoPolygon.head())    
    column = input("What column?==> ")
    city = input("What row?==> ")   
    geoPolygon = geoPolygon[geoPolygon[column] == city]
    geoPolygon = geoPolygon.dropna(axis=1)
    print(geoPolygon.head(20))
    isUnary = input("Do you wan to make a UNARY UNION(y)?==> ")
    if isUnary=="y":
      geoPolygon = geoPolygon.unary_union
      df = pd.DataFrame({"NAME" : "polygon", "polygon": geoPolygon})
      geoPolygon = gpd.GeoDataFrame(df, geometry="polygon")
      print("GeoDataFrame Series saved")
    else:
      print("GeoDataFrame selected")
  elif isCity==("u" or "union"):
    geoPolygon =geoPolygon.unary_union
    df = pd.DataFrame({"NAME" : "Interested Polygon", "polygon": geoPolygon})
    geoPolygon = gpd.GeoDataFrame(df, geometry="polygon")
    print("GeoDataFrame saved")
  else:
    print("No specified city, just a GeoPandasDF without nan values in geometry")
  pointsWhitinTheZone = SpatialJoin(Points,geoPolygon)
  exitName = "{}.csv".format(exitName)
  pointsWhitinTheZone.to_csv(exitName)
  print("data points within the polygon printed")
  polyPrint = input("Do you want to print the polygon (y)?==> ")
  if polyPrint == "y":
    polyName = input("Polygon name?==>")
    geoPolygon.to_file(filename='{}.shp'.format(polyName), driver="ESRI Shapefile")
  else:
    print("No polygon printed")
  return pointsWhitinTheZone, geoPolygon
#-------------------------------------------------------------------------------
#- Cluster Processing the hereMinerTimeZone funciton
def ClusterProcess(clustersArray, timeRadius, fileNameExit, Print, city, county, state, nameFilePointsCSV="dfPoints.csv", centroidPoints=True):
  clustersPoints = []
  if centroidPoints:
    centroids = clustersArray
  else:
    centroids = makingDataFrameFromArray(clustersArray, city, county, state, Print)
    contador = 0
  for centroid in centroids.iterrows():
    columns = centroid[1]
    jsonn = hereMinerTimeZone(timeRadius, [columns.lat , columns.long])
    clustersPoints.append(jsonn)
  #- Up to here, I got the points of each cluster zone that You gave me
  #-------------------------------------------------------------------------------
  #- Geting the points to bulid a time zone with a time of radious "timeRadious"
  GDFS = []
  for jsonP in clustersPoints:
    ##center = jsonP["response"]["center"]
    points = jsonP["response"]["isoline"][0]["component"][0]["shape"]
    points = {"points" : points}
    df = pd.DataFrame.from_dict(points)
    latss =[]
    lonss = []
    for tuples in df.iterrows():      
      columns = tuples[1]
      points = columns.points
      points = points.split(",")
      lat = points[0]
      lon = points[1]
      latss.append(float(lat))
      lonss.append(float(lon))
    lat_point_list = latss
    lon_point_list = lonss
    polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
    crs = {'init': 'epsg:4269'}
    polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
    GDFS.append(polygon)
    if centroidPoints:
      contador = "centroid"
    else:
      contador = contador + 1
  if len(GDFS) == 0:
      GDFtotal = GDFS
  else:
      GDFtotal = gpd.GeoDataFrame(pd.concat(GDFS, axis=0))
  if Print:
    dfPoints.to_csv(nameFilePointsCSV)
    polygon.to_file(filename='polygon_{}_{}_s{}.shp'.format(fileNameExit, contador, timeRadius), driver="ESRI Shapefile")
  else:
    print("No csv file, just Shape file")
  return GDFtotal
#-------------------------------------------------------------------------------
#- All for one (process)
def TimeZoneProcessFromCenter(shapeFileState, excelChurchesLatLong, timeRadi, fileNameExit, city, county, state, Print=False):
  # Reading the initial documents and making a respective dataframes
  interestedPolygon, churchesCRM, centroidInterestedZone = initialDocsForCenter(shapeFileState, excelChurchesLatLong, city)
  #-----------------------------------------------------------------
  #- geting the Time Zones for each interested cluster
  listGDF = []
  x = timeRadi[0]
  timeRadius = []
  while x < timeRadi[1]:
    timeRadius.append(x)
    x = x + 300
  timeRadius = sorted(timeRadius, reverse = True)
  listDifferenceZones = []
  for timeRad in timeRadius:
    GDF = pd.DataFrame(ClusterProcess(centroidInterestedZone, timeRad, fileNameExit,  city, county, state, Print, centroidPoints=True))
    listGDF.append(GDF)
    beforTimeRad = timeRad - 300
    if beforTimeRad>= 300:
      diffTime = "{}_{}".format(timeRad, beforTimeRad)
      listDifferenceZones.append(diffTime)
    else:
      print("Center")
  GDFtotal = pd.concat(listGDF, axis=0)
  #-----------------------------------------------------------------
  #-Geting the points inside the interested polygon (city/county)
  listNumberofZone = ["centroid"]
  df = makingZonePoints(listNumberofZone, listDifferenceZones, nameFileExit= fileNameExit, pathPointsFileExcel= r"initialChurchesLA.xlsx")
  #-----------------------------------------------------------------
  #- Preparing the data to the Machine Learning Code
  df = df[[
          "lat", 
          "long", 
          "Time"
          ]]
  clustersInterested, dataFrame = clusterMachineLearning(df, numberOfClusters=7)
  clustersDataFrame = makingDataFrameFromArray(clustersInterested, city, county, state, Print=True)
  return GDFtotal , dataFrame, clustersDataFrame
#-------------------------------------------------------------------------------
#--> Getting the points inside the two polygons in the same shapefile
def pointsInMergedZones(shapeFilePath, cityCluster, countyCluster, stateCluster):
  geoPolygon = mergingTwoPolygonsByCities(shapeFilePath)
  namePointsFileInit = input("What is the name of your excel? = ")
  namePointsFileInit = r"{}.xlsx".format(namePointsFileInit)  
  printPointsInZone = input("Do you want to write the points inside the new polygon in a CSV? yes ==> y = ")  
  numberOfClusters = input("What are the number of clusters? =" )
  numberOfClusters = int(numberOfClusters)
  Points = pd.read_excel(namePointsFileInit).set_index("NAME")
  #----------------------------------------------
  #--> Points inside the polygon
  pointsWhitinTheZone = pd.DataFrame(SpatialJoin(Points,geoPolygon))
  if printPointsInZone == "y":
    exitNamePoints = input("What is the name for the new points file CSV, in side the new polygon ? =")
    exitNamePoints = r"{}.csv".format(exitNamePoints)
    pointsWhitinTheZone.to_csv(exitNamePoints)
    print("Points writed in csv file with the name {}".format(exitNamePoints))
  else:
    print("No printed points")
  #----------------------------------------------
  #--> Preparing the data for the Machine Learning code
  pointsWhitinTheZone = pointsWhitinTheZone.drop(["index_right"], axis=1)
  pointsWhitinTheZone= pointsWhitinTheZone[["lat","long"]]
  #----------------------------------------------
  #--> Making the clustering by Machine Learning Cluster (K - Means) algorithm
  clustersInterested, dataPoints = clusterMachineLearning(pointsWhitinTheZone, numberOfClusters)
  #----------------------------------------------
  #--> Creating a dataframe with the cluster points
  clustersDataFrame = makingDataFrameFromArray(clustersInterested, cityCluster, countyCluster, stateCluster)
  return dataPoints, clustersDataFrame
#-------------------------------------------------------------------------------
#--> function to setting up the process to get the distance and traveltime
#- from the centroid to the interested point
def pointsWithTravelTimeFromCentroid(excelInitPoints, shapeFile, exitTravelPointsName, cityCluster, countyCluster, stateCluster,subsetPolygonsCreated=True):
  interestedPoints = pd.read_excel(excelInitPoints).set_index("NAME")
  numberOfClusters = input("What is the number of Clusters?")
  if subsetPolygonsCreated:
    centroid = gpd.read_file(shapeFile).unary_union
  else:
    centroid = mergingTwoPolygonsByCities(shapeFile).unary_union
  dfPoints = travelPointsFrom2Waypoints(centroid, interestedPoints, exitTravelPointsName)
  dfPoints.index.name = "NAME"
  dfPreparingPoints = preperingDataFrameToML(dfPoints)
  clustersInterested, dataPoints = clusterMachineLearning(dfPreparingPoints, numberOfClusters)
  clustersDataFrame = makingDataFrameFromArray(clustersInterested, cityCluster, countyCluster, stateCluster)
  return dataPoints, clustersDataFrame
#-------------------------------------------------------------------------------
#--> function to get the points inside the 
def pointsWithTravelTimeFromSeveralCentroids(shapeFilePath, fileChurchesLatLong, city, exitName, exitTravelPointsName):
  interestedPolygon, interestedPoints, centroidInterestedZone = initialDocsForCenter(shapeFilePath, fileChurchesLatLong, city)
  isMultiCentroid = input("Do you want multi centroids within the polygon (y) or just a single centroid (n)?==>")
  #-- Multicentroids
  if isMultiCentroid == "y":
    pathCentroids = input("What is the full name of the file of the centroids?==>")
    if ".xlsx" in pathCentroids:
      centroidInterestedZone = pd.read_excel(pathCentroids)
    elif ".csv" in pathCentroids:
      centroidInterestedZone = pd.read_csv(pathCentroids)
    else:
      centroidInterestedZone = pathCentroids
  else:
    print("Using the center of the polygon as centroid")
  #----------------------------
  #-- polygons or multipolygons and points inside that polygon
  isUnaryPolygon = input("Do you have a interested zone (y) or you want to create one(n)?==>")
  if isUnaryPolygon == "y":
    pointsWhitinTheZone, polygon = pointsWithinPolygon(interestedPoints, interestedPolygon, exitName)
  else:
    polygon = mergingTwoPolygonsByCities(interestedPolygon, isPolygonAvaible=True)
    pointsWhitinTheZone, polygon = pointsWithinPolygon(interestedPoints, polygon, exitName)
  #----------------------------
  listDfPoints = []
  for rows in centroidInterestedZone.iterrows():
    centroid = [rows[1]["lat"], rows[1]["long"]]
    dfPoints = travelPointsFrom2Waypoints(polygon, centroid, pointsWhitinTheZone, exitTravelPointsName)
    listDfPoints.append(dfPoints)
  dfAllPointsTime = pd.concat(listDfPoints, axis=1, join='outer')
  dfAllPointsTime.to_csv("AllpointsTime{}.csv".format(exitTravelPointsName))
  return dfAllPointsTime
#-------------------------------------------------------------------------------
#--> Process to Machien Learning
def processML(dataPointsFullName, cityCluster, countyCluster, stateCluster, numberOfClusters):
  if ".xlsx" in dataPointsFullName:
    dfPoints = pd.read_excel(dataPointsFullName)
  elif ".csv" in dataPointsFullName:
    dfPoints = pd.read_csv(dataPointsFullName)
  else:
    dfPoints = dataPointsFullName
  #----------------------------
  dfPreparingPoints = preperingDataFrameToML(dfPoints)
  clustersInterested, finalPoints = clusterMachineLearning(dfPreparingPoints, numberOfClusters)
  clustersDataFrame = makingDataFrameFromArray(clustersInterested, cityCluster, countyCluster, stateCluster)
  return finalPoints, clustersDataFrame
#-------------------------------------------------------------------------------