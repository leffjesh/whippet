# whippet
implementation of the WHIPPET invasive plant eradication prioritization tool

background information is available at:

-http://www.ncbi.nlm.nih.gov/pubmed/20832930
-http://whippet.cal-ipc.org/pages/view/guide
-http://proceedings.esri.com/library/userconf/proc14/papers/223_620.pdf

tool devleoped by Gina Darin
implemented in python for use in ESRI workflows by @leffjesh


Requirements:

You must have ArcGIS installed in order to use this. Developed with ArcGIS 10.2.2 install, but probably works on older versions.

Setup:

-Download this repository using the "Download Zip" link on the right
-In ArcGIS right-click in ArcToolbox window and select "Add Toolbox". Then navigate to the unzipped folder that you just downloaded.  The toolbox should now appear in your ArcToolbox window.
-You will first need to setup your species scores using the WHIPPET Species Assessment Form and placing the values into the species_scores.csv file that is included in this repository.
-You can then load the various layers needed for whippet evaluation (mines, roads, streams/rivers, weed populations, site values) and run the tool.


Documentation remains to be gathered and/or completed before this tool is useful. 