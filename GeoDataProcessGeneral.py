#---------------------------------------------------------------------------
#---- Random point generator-----------------------------------------------
# importing the shapely module
from shapely.geometry import Point
# importing the module geopandas
import geopandas as gpd
from pprint import pprint
import numpy as np
from geocoderYelp import *
import pandas as pd
import numpy as np
# Creating a new function called "randPoints"
def randPoints(array):
    """
    This is a function to create random points, using the initial array as a seed
    """
    # "Points" is a vacuum list
    Points = []
    # iteration over random points array
    # In this iteration we area creating a object Point
    # Then, you save all the objects random points in a list called "Points"
    for row in np.nditer(array):
        P = Point (row[0], row[1])
        Points.append(P)
    return Points
#------------------------------------------------------------------------------
# creating the geodataframe converter for the points wihtin the opp zone
def MakingPoints(points, interestedGeoZone):
    """ 
    Function to take the points inside a intesred zone,
    to do this you need the georeferenced points and 
    the geodataframe of the interested zone
    """
    # Creating a empty geodataframe
    gdf = gpd.GeoDataFrame()

    # Adding the points to the geometry column in the new gdf 
    gdf.geometry = points

    # Adding the crs to the new gdf
    # Note = The crs have to be the same crs as the opportunity zone
    gdf.crs = interestedGeoZone.crs
    # Now, we have the same crs, so we can make a spatial join between geodataframes
    # Making a spatial join between the polygo (opp zone) and the random points
    # using the attribute 'within' we join only the points 
    # that have the coordinates within the polygon (opp zone)
    join = gpd.sjoin( gdf,interestedGeoZone,  op="within")
    return join
#------------------------------------------------------------------------------
#------ Points from the square ----------------------------------------------
### Making a simple random long/lat generator
# function to generrate random coordinates
# the x0,y0 are the center of the centroid
# d is the distance between the centroid and the max point
# k is a scale factor to correct the random number (within the same point decimal)
# size is the number of points that you want to generate
def square_rand(x0,y0,size,dist,seed):
    """
    In this function you ontain two arrays of points,
    to do that you nned to say the initial points of the square (x0 and y0),
    the size of the square (length of one side),
    the distance between points (dist),
    and the a seed
    """
    k = dist * 2
    np.random.seed(seed)
    rx = np.random.random(size)
    ry = np.random.random(size)
    xup = x0 + k*rx 
    yup = y0 + k*ry
    xdw = x0 - k*rx 
    ydw = y0 - k*ry    
    xd = np.vstack((xup,xup, xdw,xdw))
    yd = np.vstack((yup,ydw,yup,ydw))
    return xd, yd
#------------------------------------------------------------------------------
#-------- Calling for the random points ---------------------------------------
#----------------------------------
# -- making the call to the api ---
def YelpCaller(GeoDataFrame, exitPath, rad, limit, term, categorie, locations):
    list_opp = []
    for tupla in GeoDataFrame.iterrows():
        #-- for each tuple look for the rows
        row = tupla[1]
        #- from this row look for the geometry point         
        #lon = row.Longitude
        lon = row.geometry.x
        #lat = row.Latitude
        lat = row.geometry.y
        #lat = 37.82078417006873
        #lon = -122.2733870924242
        # --setting up the radius and limits
        radius = rad 
        limits = limit
        term = term
        offset= 5
        loc = locations
        # -- calling the last two functions
        r = YelpMiner(lat, lon, radius, limits, term, categorie=categorie, location=loc, offsets=offset)
        #pprint(r)
        res = YelpRespond(r)
        # -- writting the dictionaries in dataframes
        df = pd.DataFrame.from_dict(res, orient='index')
        df.index.name = "Name"
        list_opp.append(df)
    #-- Saving the dataframe
    dfT = pd.concat(list_opp, axis=0, sort=False)
    if len(dfT) > 0:
        dfT = dfT.drop_duplicates()
        dfT.to_csv(exitPath)
    else:
        print("empty")        
    return dfT
#------------------------------------------------------------------------------
#------------- Spatial Join Function --------------------------------------
# importing the module geopandas
# creating the geodataframe converter for the points wihtin the opp zone
def SpatialJoin(dataframe1, Geodataframe2):
    """This function makes a merge between the points inside the geospatial zone in the geodataframe2. 
    To do this, First, it´s necesary it's necesary translate the String with the lat/long info to a strings that geopandas could read, 
    then I make a geodataframe with this new points in order to make a spatial join between this geodataframes """
    #MakingPoints(dataframe1, Geodataframe2)
    Points = []
    for rows in dataframe1.iterrows():
        row = rows[1]
        P = Point (row['long'], row['lat'])
        Points.append(P)
    Geodataframe1 = gpd.GeoDataFrame(dataframe1)
    Geodataframe1.geometry = Points
    # Note = The crs have to be the same crs as the opportunity zone
    # Setting up the two geodataframe with the same crs
    Geodataframe1.crs = Geodataframe2.crs
    # Now, we have the same crs, so we can make a spatial join between geodataframes
    # Making a spatial join between the polygon and the random points
    # using the attribute 'within' we join only the points 
    # that have the coordinates within the polygon (opp zone)
    join = gpd.sjoin(Geodataframe1, Geodataframe2 ,  how="inner", op='within')
    return join
#-------------------------------------------------------------------------------------------------
#-------Reading files from two spatial zones, one from a geodataframe and other from Excel file --
def MergingZones1Zones2Files(pathZones1, pathZones2, Cities_CountiesPath, CensusGeoPath):
    columns = ['State','County',  'GEOID',  'Tract type','ACS data source']
    dfZones1 = pd.read_excel(pathZones1)
    dfZones1 = df.drop(df.index[0:4])
    #-------------------------------------------------
    #-- Indexing just the California's GEOIDs
    dfZones1.columns = columns
    dfZones1State = df[df.State[:] == 'California']
    #-------------------------------------------------
    #------- Splintting the GEOID --------------------
    ## Creating the list with the GEOID number as strings
    geoid = []
    for x in df_opp['GEOID']:
        y = str(x)
        geoid.append(y)
    #--------------------------------------------------
    #-----------------------------------------------------
    ## Spliting each GEOID string in three parts, the STATE + COUNTY + TRACT
    state = [] # THe list with the state code
    county = [] # THe list with the county code
    tract = [] # THe list with the tract code
    for x in geoid:
        state.append(x[:2])
        county.append(x[2:5])
        tract.append(x[5:12])
    #---------------------------------------------------------
    #---Appending the state, county and tract codes to the dfZones1
    dfZones1_id = dfZones1.assign(Tract_num=pd.Series(tract).values)
    dfZones1_id = dfZones1.assign(County_num=pd.Series(county).values)
    dfZones1_id = dfZones1.assign(State_num=pd.Series(state).values)
    #---------------------------------------------------
    #---------------------------------------------------
    #---------- Reading the excel file with dfZones2 cities
    df2 = pd.read_excel(pathZones2)
    df2.rename(columns={'California Cities':'Name'}, inplace=True)
    #--Creating a news dataframes with a, b and c with their respectives cities
    dfZones2_a = df2['a']
    dfZones2_b = df2["b"]
    dfZones2_c = df2['c']
    dfZones2_d = df2['d']
    dfZones2_e = df2['e']
    dfZones2_cities = pd.concat([dfZones2_a,dfZones2_b, dfZones2_c, dfZones2_d, dfZones2_e], axis=0, join="outer")
    #--Cleaning the news DF, taking off all the NAN values
    dfZones2_a = pd.DataFrame(dfZones2_a.dropna())
    dfZones2_b = pd.DataFrame(dfZones2_b.dropna())
    dfZones2_c = pd.DataFrame(dfZones2_c.dropna())
    dfZones2_cities = pd.DataFrame(dfZones2_cities).dropna()
    dfZones2_cities = dfZones2_cities.drop_duplicates()
    #-- Renaming the a,b or c columns in order to merge this df with the cities and counties df
    dfZones2_a.rename(columns={'a':'Name'}, inplace=True)
    dfZones2_b.rename(columns={'b':'Name'}, inplace=True)
    dfZones2_c.rename(columns={'c':'Name'}, inplace=True)
    dfZones2_cities.rename(columns={0:'Name'}, inplace=True)
    #----------------------------------------------------------
    ## reading the excel file with cities and counties of California
    df_cit_count = pd.read_excel(Cities_CountiesPath)
    #----------------------------------------------------------
    ## Merging the dfZones2 cities with their respectives counties for each company
    dfZones2_cities_counties = pd.merge(df_cit_count, dfZones2_cities, on =['Name'])
    ### For a
    dfZones2_a_cities_counties = pd.merge(df_cit_count, dfZones2_a, on =['Name'])
    dfZones2_a_cities_counties = dfZones2_a_cities_counties.dropna()
    ## For b
    dfZones2_b_cities_counties = pd.merge(df_cit_count, dfZones2_b, on =['Name'])
    dfZones2_b_cities_counties = dfZones2_b_cities_counties.dropna()
    ## For c
    dfZones2_c_cities_counties = pd.merge(df_cit_count, dfZones2_c, on =['Name'])
    dfZones2_c_cities_counties = dfZones2_c_cities_counties.dropna()
    #-----------------------------------------------------------
    ## Merging the dfZones1 zones with the dfZones2 counties
    dfZones1_Zones2_cities = pd.merge(dfZones2_cities_counties, dfZones1_id, on='County')
    ## Creating a new DF without GEOID duplicates 
    dfZones1_Zones2_cities_sd = dfZones1_Zones2_cities.drop_duplicates(subset='GEOID')
    dfZones1_Zones2_cities_sd = dfZones1_Zones2_cities_sd.reset_index(drop=True)
    ## For a
    dfZones2_a_dfZones1_con_cities = pd.merge(dfZones2_a_cities_counties, dfZones1_id, on='County')
    ## Creating a new DF without GEOID duplicates 
    dfZones2_a_dfZones1_con_cities_sd = dfZones2_a_dfZones1_con_cities.drop_duplicates(subset='GEOID')
    dfZones2_a_dfZones1_con_cities_sd = dfZones2_a_dfZones1_con_cities_sd.reset_index(drop=True)
    ## For b
    dfZones2_b_dfZones1_con_cities = pd.merge(dfZones2_b_cities_counties, dfZones1_id, on='County')
    ## Creating a new DF without GEOID duplicates
    dfZones2_b_dfZones1_con_cities_sd = dfZones2_b_dfZones1_con_cities.drop_duplicates(subset='GEOID')
    dfZones2_b_dfZones1_con_cities_sd = dfZones2_b_dfZones1_con_cities_sd.reset_index(drop=True)
    ## For c
    dfZones2_c_dfZones1_con_cities = pd.merge(dfZones2_cities_counties, dfZones1_id, on='County')
    ## Creating a new DF without GEOID duplicates 
    dfZones2_c_dfZones1_con_cities_sd = dfZones2_c_dfZones1_con_cities.drop_duplicates(subset='GEOID')
    dfZones2_c_dfZones1_con_cities_sd = dfZones2_c_dfZones1_con_cities_sd.reset_index(drop=True)
    #----------------------------------------------------------
    #----------------------------------------------------------
    #-------------GEOPANDAS time-------------------------------
    # Reading the data files from the Census webpage from California State
    california_shp = gpd.read_file(CensusGeoPath)
    california_shp.crs
    #----------------------------------------------------------
    ##### Making tets for c company
    # Matching the zones with the opportunity zones
    dfZones1_Zones2_c = california_shp.merge(dfZones2_c_dfZones1_con_cities_sd, on='GEOID')
    print("dfZones1_Zones2_c len= ", len(dfZones1_Zones2_c) )
    dfZones1_Zones2_a = california_shp.merge(dfZones2_a_dfZones1_con_cities_sd, on='GEOID')
    dfZones1_Zones2_b = california_shp.merge(dfZones2_b_dfZones1_con_cities_sd, on='GEOID')
    dfZones1_Zones2_d = california_shp.merge(dfZones2_c_dfZones1_con_cities_sd, on='GEOID')
    # Matching the zones with the opportunity zones
    dfZones1_Zones2_a.to = california_shp.merge(dfZones2_a_dfZones1_con_cities_sd, on='GEOID')
    dfZones1_Zones2_b.to = california_shp.merge(dfZones2_b_dfZones1_con_cities_sd, on='GEOID')
    dfZones1_Zones2_c.to = california_shp.merge(dfZones2_c_dfZones1_con_cities_sd, on='GEOID')
    #Writting the geodataframes ----------------------------
    dfZones1_Zones2.to_file("dfZones1_Zones2_geodataframe")
    dfZones1_Zones2_c.to_file("dfZones1_Zones2_c_geodataframe")
    dfZones1_Zones2_b.to_file("dfZones1_Zones2_b_geodataframe")
    dfZones1_Zones2_a.to_file("dfZones1_Zones2_a_geodataframe")
    #-Merging complete-------------------------------------
    return dfZones1_Zones2
    #------------------------------------------------------
def Zones1GEOID(listaGEOID, Zones1, size, Date, folderExit, term, categorie, location, radius):
    dfls = []
    for rows in list(Zones1.iterrows())[ listaGEOID[0] : listaGEOID[1] ]:
        columns = rows[1]
        GEOID = columns.GEOID
        zones1 = Zones1[Zones1.GEOID == str(GEOID)]
        centroid = zones1.centroid
        #-----------------------------------------------------
        # importingt shapely to creat the max point
        from shapely.geometry import Point
        # Creating the max points using the coordinates from the bounds in the opportunity zones
        zones1_maxBounds = Point(zones1.bounds.maxx, zones1.bounds.maxy)
        # Getting the distance from the centroid to the further point
        rad_zones1 = centroid.distance(zones1_maxBounds)
        rad_zones1 = rad_zones1.iloc[0]
        x0 = float(centroid.x)
        y0 = float(centroid.y)
        # Generating the points to cover the zones1
        SquarePoints = square_rand(x0, y0, size, rad_zones1, seed=48)
        # radom choosing from the generated points
        RandomPoints = randPoints(SquarePoints)
        # Making a geodataframe with the random points and making a spatial join
        gdf = MakingPoints(RandomPoints, zones1)
        # Making the geodtaframe in a 
        df = pd.DataFrame(gdf)
        #GeoDataFrame = df
        GeoDataFrame = [x0, y0]
        rad = radius
        limit = 50
        loc  = "{},California".format(str(columns.Name))
        exitPath = r"{}\YelpCallerResponse{}_d{}.csv".format(folderExit, GEOID,  Date)
        print("YelpCaller")
        dff = YelpCaller(GeoDataFrame, exitPath, rad, limit, term, categorie, loc)
        if len(dff) > 0 :
            df2 = SpatialJoin(dff, zones1)
            dft = pd.DataFrame(df2)
            pathExith = r"{}\zones1GEOID{}_d{}.csv".format(folderExit, GEOID,  Date)
            dft.to_csv(pathExith)
            dfls.append(df2)
            print("len = ",len(dft))
        else:
            print("empty sjoin")                        
        print("----------------FINISH GEOID-----------------------")
    return dfls
#------------------------------------------------------------------------------
#-------- Calling for the random points with OFFset---------------------------------------
#----------------------------------
# -- making the call to the api ---
def YelpCallerOffset(Centroid, exitPath, rad, limit, term, categorie, locations):
    list_opp = []
    x0 = Centroid[0]
    y0 = Centroid[1]
    start = 0
    end = 19
    for contador in range(start, end):
        #- Coordinates of the centroid
        lon = x0
        #lat = row.Latitude
        lat = y0
        # --setting up
        offset= contador * 49
        loc = locations
        # -- calling the last two functions
        r = YelpMiner(lat, lon, radius= rad, limits=limit, term=term, categorie=categorie, location=loc, offsets=offset)
        #pprint(r)
        res = YelpRespond(r)
        # -- writting the dictionaries in dataframes
        df = pd.DataFrame.from_dict(res, orient='index')
        df.index.name = "Name"
        list_opp.append(df)
    #-- Saving the dataframe
    dfT = pd.concat(list_opp, axis=0, sort=False)
    if len(dfT) > 0:
        dfT = dfT.drop_duplicates()
        dfT.to_csv(exitPath)
    else:
        print("empty")        
    return dfT
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def ZoneGEOIDOffSet(listaGEOID, zones, size, Date, folderExit, term, categorie, location, radius):
    dfls = []
    for rows in list(Opp_zones.iterrows())[ listaGEOID[0] : listaGEOID[1] ]:
        columns = rows[1]
        GEOID = columns.GEOID
        zone = zones[Opp_zones.GEOID == str(GEOID)]
        centroid = zone.centroid
        #-----------------------------------------------------
        # importingt shapely to creat the max point
        from shapely.geometry import Point
        # Creating the max points using the coordinates from the bounds in the zones
        zone_maxBounds = Point(opp_zone.bounds.maxx, opp_zone.bounds.maxy)
        # Getting the distance from the centroid to the further point
        rad_opp_zone = centroid.distance(opp_zone_maxBounds)
        rad_opp_zone = rad_opp_zone.iloc[0]
        x0 = float(centroid.x)
        y0 = float(centroid.y)
        Centroid = [x0, y0]
        rad = radius
        limit = 50
        loc  = "{},California".format(str(columns.Name))
        exitPath = r"{}\YelpCallerResponse{}_d{}.csv".format(folderExit, GEOID,  Date)
        print("YelpCaller")
        dff = YelpCallerOffset(Centroid, exitPath, rad, limit, term, categorie, loc)
        if len(dff) > 0 :
            df2 = SpatialJoin(dff, opp_zone)
            dft = pd.DataFrame(df2)
            pathExith = r"{}\OppZoneGEOID{}_d{}.csv".format(folderExit, GEOID,  Date)
            dft.to_csv(pathExith)
            dfls.append(df2)
            print("len = ",len(dft))
        else:
            print("empty sjoin")                        
        print("----------------FINISH GEOID-----------------------")
    return dfls
#------------------------------------------------------------------------------
