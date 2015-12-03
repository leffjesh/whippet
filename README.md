#whippet
implementation of the WHIPPET invasive plant eradication prioritization tool devleoped by Gina Darin and background information is available at:

- http://www.ncbi.nlm.nih.gov/pubmed/20832930
- http://whippet.cal-ipc.org/pages/view/guide

You must read these resources to understand this tool. Implemented as a ESRI Python Toolbox for use in ESRI workflows by Jeff Lesh.

##Requirements:

You must have ArcGIS installed in order to use this. Developed with ArcGIS 10.2.2 install, but probably works on older versions.

##Setup/Installation:

1. Download this repository using the "Download Zip" link on the right
2. In ArcGIS right-click in ArcToolbox window and select "Add Toolbox". Then navigate to the unzipped folder that you just downloaded.  The toolbox should now appear in your ArcToolbox window.

##Usage:

1. You will first need to setup your species scores using the WHIPPET Species Assessment Form and placing the values into the species_scores.csv file that is included in this repository. 

###Other details:

- Distances and area criteria "breaks" are used in calculating Conspecific score, Vector (mines, streams, streets) score, and Population Sizes scores with the following options: 
--*Vector Breaks

| Option Name | Unit | Score | Min Unit Measurement | Max Unit Measurement |
| -------------------------- | ------- | ------- | ------- | --- |
| distance option 1 (miles) | Mile | 10 | 0 | 0.1 |
|   |  | 6 | 0.1 | 1 |
|   |  | 3 | 1 | 10 |
|   |  | 1 | 10 | 25 |
|   |  | 0 | 25 | ~ |
| distance option 2 (miles) | Mile | 10 | 0 | 0.05 |
|   |  | 6 | 0.05 | 0.5 |
|   |  | 3 | 0.5 | 5 |
|   |  | 1 | 5 | 12.5 |
|   |  | 0 | 12.5 | ~ |
| distance option 3 (miles) | Mile | 10 | 0 | 0.01 |
|   |  | 6 | 0.01 | 0.1 |
|   |  | 3 | 0.1 | 1 |
|   |  | 1 | 1 | 5 |
|   |  | 0 | 5 | ~ |
| distance option 4 (miles) | Mile | 10 | 0 | 0.01 |
|   |  | 6 | 0.01 | 0.05 |
|   |  | 3 | 0.05 | 0.1 |
|   |  | 1 | 0.1 | 1 |
|   |  | 0 | 1 | ~ |
| conspecifics option 1 (miles) | Mile | 10 | 0 | 0.1 |
|   |  | 6 | 0.1 | 1 |
|   |  | 3 | 1 | 10 |
|   |  | 1 | 10 | 25 |
|   |  | 0 | 25 | ~ |
| conspecifics option 2 (miles) | Mile | 10 | 0 | 0.05 |
|   |  | 6 | 0.05 | 0.5 |
|   |  | 3 | 0.5 | 5 |
|   |  | 1 | 5 | 12.5 |
|   |  | 0 | 12.5 | ~ |
| conspecifics option 3 (miles) | Mile | 10 | 0 | 0.01 |
|   |  | 6 | 0.01 | 0.05 |
|   |  | 3 | 0.05 | 0.1 |
|   |  | 1 | 0.1 | 1 |
|   |  | 0 | 1 | ~ |
| conspecifics option 4 (miles) | Mile | 10 | 0 | 0.001 |
|   |  | 6 | 0.001 | 0.01 |
|   |  | 3 | 0.01 | 0.1 |
|   |  | 1 | 0.1 | 1 |
|   |  | 0 | 1 | ~ |
| area option 1 (acres) | Acre | 10 | 0 | 0.1 |
|   |  | 6 | 0.1 | 1 |
|   |  | 3 | 1 | 10 |
|   |  | 1 | 10 | 100 |
|   |  | 0 | 100 | ~ |
| area option 2 (acres) | Acre | 10 | 0 | 0.05 |
|   |  | 6 | 0.05 | 0.5 |
|   |  | 3 | 0.5 | 5 |
|   |  | 1 | 5 | 50 |
|   |  | 0 | 50 | ~ |
| area option 3 (acres) | Acre | 10 | 0 | 0.1 |
|   |  | 6 | 0.1 | 0.5 |
|   |  | 3 | 0.5 | 1 |
|   |  | 1 | 1 | 10 |
|   |  | 0 | 10 | ~ |



- Patch size should be *gross patch size* supported units are sq. feet (tested in this), meters, acres.
- All attribute scores should be normalized to 10, with one exception.  When using a raster layer normalize to 1000 (it will be automatically adjusted appropriately).
- If you don't have Accessibility data and/or Patch Size attributes for your invasive species dataset, you may still run this tool with the following modifications.  Create attributes of field type Long, Short, Double, or Float for these criteria and leave the value for each observation set to "Null".  Open the whippet_toolbox.pyt script in a text editor and modify the following values: 
```
default_population_score = 10
default_accessibility_score = 3
```

##Caveats

- This was tested using only sq. feet patch size data.
