#whippet
implementation of the WHIPPET invasive plant eradication prioritization tool

WHIPPET devleoped by Gina Darin and background information is available at:
-http://www.ncbi.nlm.nih.gov/pubmed/20832930
-http://whippet.cal-ipc.org/pages/view/guide
-http://proceedings.esri.com/library/userconf/proc14/papers/223_620.pdf

Implemented as a ESRI Python Toolbox for use in ESRI workflows by Jeff Lesh

##Requirements:

You must have ArcGIS installed in order to use this. Developed with ArcGIS 10.2.2 install, but probably works on older versions.

##Setup:

-[Download this repository using the "Download Zip" link on the right]
-[In ArcGIS right-click in ArcToolbox window and select "Add Toolbox". Then navigate to the unzipped folder that you just downloaded.  The toolbox should now appear in your ArcToolbox window.]

-You will first need to setup your species scores using the WHIPPET Species Assessment Form and placing the values into the species_scores.csv file that is included in this repository.

-You can then load the various layers needed for whippet evaluation (mines, roads, streams/rivers, weed populations, site values) and run the tool.

Usage:

Data prep:
If you don't have Accessibility data and/or Patch Size attributes for your invasive species dataset, you may still run this tool with the following modifications.  Create attributes of field type Long, Short, Double, or Float for these criteria and leave the value for each observation set to "Null".  Open the whippet_toolbox.pyt script in a text editor and modify the following values: 

default_population_score = 10
default_accessibility_score = 3



Run tool:

Documentation remains to be gathered and/or completed before this tool is useful. 
