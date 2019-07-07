# GIS points within maps
![](https://img.shields.io/github/issues/pedroortizortega/GIS-points-within-maps.svg) ![](https://img.shields.io/github/forks/pedroortizortega/GIS-points-within-maps.svg) ![](https://img.shields.io/github/tag/pedroortizortega/GIS-points-within-maps.svg) ![](https://img.shields.io/github/release/pedroortizortega/GIS-points-within-maps.svg) ![](https://img.shields.io/github/stars/pedroortizortega/GIS-points-within-maps.svg)

This code is to look for points inside some geographical zone in California. I used  a clusterin machine learning algorimth to classify the nearest neighbors in distance, obtain a cluster. And, from the center of the cluster make masure the travel time. With this flag I can obtain an approcimation of the time between points and said a range of time to travel between one point to another.

**Table of Contents**

[TOC]

## Description
###  GeoPandasProcess file
Within this file I looked into the Census Bureau file I could find some geographical identifier for this interesting zones. So, the next task was looking for the coordinates in the GeoJSON/shapefile to map them using GeoPandas. With this library I could map all the leads into a California's map. 

### Clustering Points file
Now, studying the data and talking with the sales team, we decided to make a classifier to design new routes to the sales personnel. With these new lists, we want to create the new dates for the personnel in the field to visit the leads. So, to create these zones; first, I used a clustering model (Scikit Learn) to find the center of this new zone, I found 7 possible zones. Then, I used a API HERE to obtain the time travel between the center of the cluster and the interested point. Then, I create a function to make a flag time where I could said an approximation time between two points inside the cluster (a polygon - area) . 

I mean, imagine that you are calling with a new possible client and you get the address from this guy, so you type the address and the dashboard draw the point over the map and put into one of these new zones (clusters), after that the dashboard tells you what are the nearest neighbors in time from the location of your client, so you can attach a new date in the calendar (to visit they) with the information of the dashboard. 

## Used Libraries
- Pandas
- GeoPandas
- SciKit Learn
- requests (for APIs REST)
- Shapely
- Numpy
- BeautifulSoup
- Prety print
- Glob
- json
- re

## Modelig in Machine Learning
I used the library SciKit Learn to create a function that create the clusters
- K-Means clustering


