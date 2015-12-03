'''
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
   
   Based on WHIPPET ,
   Coding by Jeff Lesh jeff@jefflesh.com, http://github.com/leffjesh
   Hosted on github, contributions welcome
   
   potential enhancement to consider: rather than use nearest conspecific, use a more sophisticated way to determine priority based on how close a population is to another conspecific one
       ideas
           -calc distance to all conspecific pops, 
           -assign populations to clusters and calc distance to nearest cluster or to all clusters
           -assign to clusters, then create a graph (think graph theory) of clusters with relevant vectors as pathways, then calculate distance to nearest neighbor along pathway
   
'''
import arcpy
from arcpy.sa import *
import time
import datetime
import csv
import os
import inspect
import shutil
import numpy as np


def edit_report(report_name, output_dir, replacements, new_report_name=None):
    report_templates = os.path.dirname(__file__) 
    filename = report_templates + "/" + report_name + ".html"
    if not os.path.isfile(filename):
        return False 
    
    f = open(filename)
    text = f.read()
    for replacer in replacements:
        text = text.replace(replacer[0], replacer[1])
    
    if new_report_name:
        report_name = new_report_name
    f2 = open (output_dir + "/"+report_name + ".html", "w")
    f2.write(text)
    f.close
    f2.close
    return True

def score_using_breaks (value, breaks, conversion_multiplier=5280):#defaults to sq ft to miles conversion
    #TODO: order breaks automatically to ensure structure
    for criteria in breaks:
        if len(criteria)==1:#last option
            return criteria[0]
        if value < (criteria[1] * conversion_multiplier):
            return criteria[0]
    return False


def get_conversion_num (unit, breaks_option):
    unit = unit.lower()
    breaks_option = breaks_option.lower()
    
    if unit == "square feet" and "acres" in breaks_option:
        return 43560
    elif (unit == "acre" and "acres" in breaks_option) or (unit == "square meter" and "square meters" in breaks_option) or (unit == "hectare" and "hectares" in breaks_option):
        return 1
    elif unit == "square meter" and "hectares" in breaks_option:
        return 10000
    elif unit == "feet" and "mile" in breaks_option:
        return 5280
    elif (unit == "feet" and "feet" in breaks_option) or (unit == "meter" and "meter" in breaks_option) or (unit == "mile" and "mile" in breaks_option):
        return 1
    else:
        print "error, bad patch size unit.  this may be due to the linear unit of your weed layer's projection, tested with international feet"
        return False
    
def vector_scored (risk_scores,weights,values):
    # vector scores are only valid if this species is affect by the associated vector
    
    score = 0
    vectors = []
    #only analize vectors which are deemed relevant for this species
    if risk_scores[11] == "yes":
        vectors.append("streets")
    if risk_scores[12] == "yes":
        vectors.append("rivers")
    if risk_scores[13] == "yes":
        vectors.append("mines")
    
#     total = sum(map(lambda x: weights[x], vectors)) this alternate methodology was rejected
    
    for vector in vectors:
        #         weights[vector]=weights[vector]/total  # this idea was vetoed, because it would reward species with only on vector over species with multiple in a way
        score = score + weights[vector] * values[vector]
    
    return score

def calculate_scores(source_layer, target_layer,layer_name,breaks, conversion_num):
    try:
        fields = []
        fieldList = arcpy.ListFields(source_layer)
        for field in fieldList:
            fields.append(field.name)
            
        arcpy.Near_analysis(source_layer,target_layer)
        
        if not layer_name+"_score" in fields:
            arcpy.AddField_management(source_layer,layer_name+"_score","SHORT")
            
        arcpy.DeleteField_management (source_layer,"NEAR_FID")
        
        weeds = arcpy.UpdateCursor(source_layer)
        for weed in weeds:
            weed.setValue(layer_name+"_score",score_using_breaks(weed.getValue("NEAR_DIST"), breaks, conversion_num) )
            weeds.updateRow(weed)
        
        arcpy.DeleteField_management (source_layer,"NEAR_DIST")
        del weed, weeds
        
    except:
        print arcpy.GetMessages()
        
class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Whippet_Toolbox"
        self.alias = ""
        # List of tool classes associated with this toolbox
        self.tools = [Whippet]
        
        
class Whippet(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Whippet"
        self.description = "Python implementation of WHIPPET"
        self.canRunInBackground = True

    def getParameterInfo(self):
        # First parameter
        param0 = arcpy.Parameter(
            displayName="Weed Observations",
            name="prioritization_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        param1 = arcpy.Parameter(
            displayName="Scientific Name Attribute",
            name="Scientific",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        
        param2 = arcpy.Parameter(
            displayName="Gross Patch Size Attribute",
            name="patch_size",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Accessibility Score Attribute",
            name="accessibility_score_attribute",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        
        param4 = arcpy.Parameter(
           displayName="Gross Patch Size Unit",
           name="patch_size_unit",
           datatype="GPString",
           parameterType="Required",
           direction="Input")

        param5 = arcpy.Parameter(
            displayName="Conspecific Breaks",
            name="conspecific_breaks",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        param6 = arcpy.Parameter(
            displayName="Population Breaks",
            name="population_breaks",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        param7 = arcpy.Parameter(
            displayName="site value",
            name="site_value",
            datatype=["DERasterDataset","GPRasterLayer","DERasterCatalog","GPFeatureLayer"],
            parameterType="Required",
            direction="Input")

        param8 = arcpy.Parameter(
            displayName="site value Attribute",
            name="site value_attribute",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        
        param9 = arcpy.Parameter(
            displayName="streams",
            name="streams_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        param10 = arcpy.Parameter(
            displayName="streets",
            name="streets_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        param11 = arcpy.Parameter(
            displayName="mines",
            name="mines_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param12 = arcpy.Parameter(
            displayName="Vector Breaks",
            name="vector_breaks",
            datatype="GPString",
            parameterType="Required",
            direction="Input")


        
        param0.filter.list = ["Point"]
        
        # Set the filter to accept only fields that are Short or Long type
        param1.filter.list = ['Text']
        param1.parameterDependencies = [param0.name]
        param2.filter.list = ['Long','Short','Float','Double']
        param2.parameterDependencies = [param0.name]

        param8.filter.list = ['Long','Short','Float','Double']
        param8.parameterDependencies = [param7.name]

        param3.filter.list = ['Long','Short','Float','Double']
        param3.parameterDependencies = [param0.name]
        
       
        #added raster support, so removed this
        #param7.filter.list = ["Polygon"]
        
        param9.filter.list = ["Polyline"]
        param10.filter.list = ["Polyline"]
        param11.filter.list = ["Point"]
        
        param12.defaultEnvironmentName="distance option 1 (miles)"
        param12.filter.list=['distance option 1 (miles)',
                            'distance option 2 (miles)',
                            'distance option 3 (miles)',
                            'distance option 4 (miles)'
                            ]  
        
        param5.defaultEnvironmentName='conspecifics option 1 (miles)'
        param5.filter.list=['conspecifics option 1 (miles)',
                            'conspecifics option 2 (miles)',
                            'conspecifics option 3 (miles)',
                            'conspecifics option 4 (miles)']    
         
        param6.defaultEnvironmentName='area option 1 (acres)'
        param6.filter.list=['area option 1 (acres)',
                            'area option 2 (acres)',
                            'area option 3 (acres)'] 
                                                              
        param4.defaultEnvironmentName='square feet'
        param4.filter.list=["square feet","acre","square meter","hectare"]
        
        param13 = arcpy.Parameter(
            displayName="WHIPPET Results",
            name="whippet_results",
            datatype="GPFeatureLayer",
            parameterType="Derived",
            direction="Output")

        params = [param0, param1, param2,param3,param4,param5, param6,param7, param8, param9, param10,param11,param12,param13]
    
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
        prioritization_layer = parameters[0].value
        scientific_fieldname = str(parameters[1].value)
        patch_size_fieldname = str(parameters[2].value)
        accessibility_fieldname = str(parameters[3].value)
        patch_size_unit = str(parameters[4].value)
        percent_cover_fieldname = "obsPercentCover" #removed due to it not being in the original model
        conspecific_breaks = str(parameters[5].value)
        population_breaks = str(parameters[6].value)
        site_value = parameters[7].value
        site_value_fieldname = str(parameters[8].value)
        streams = parameters[9].value
        streets = parameters[10].value
        mines = parameters[11].value
        vector_breaks = str(parameters[12].value)
        
        #defaults, you may want to change these depending on your dataset, we calculated the median for our populations with pop size data and used that resulting score
        default_population_score = 10
        default_accessibility_score = 3
        
        #used when you are using a separate method for site_value calculation, set to False as default
        Multi_Factor_Site_Value = False
        
        #used for faster runs without performing certain tasks
        re_run = False
        
        break_options = {'distance option 1 (miles)':[[10,.1],
                                   [6,1],
                                   [3,10],
                                   [1,25],
                                   [0]],
                         'distance option 2 (miles)':[[10,.05],
                                   [6,.5],
                                   [3,5],
                                   [1,12.5],
                                   [0]],
                         'distance option 3 (miles)':[[10,.01],
                                   [6,.1],
                                   [3,1],
                                   [1,5],
                                   [0]],
                         'distance option 4 (miles)':[[10,.01],
                                   [6,.05],
                                   [3,.1],
                                   [1,1],
                                   [0]],
                         'conspecifics option 1 (miles)':[[0,.1],
                                   [1,1],
                                   [3,10],
                                   [6,25],
                                   [10]],
                         'conspecifics option 2 (miles)':[[0,.05],
                                   [1,.5],
                                   [3,5],
                                   [6,12.5],
                                   [10]],
                         'conspecifics option 3 (miles)':[[0,.01],
                                   [1,.05],
                                   [3,.1],
                                   [6,1],
                                   [10]],
                         'conspecifics option 4 (miles)':[[10,.001],
                                   [6,.01],
                                   [3,.1],
                                   [1,1],
                                   [0]],
                         'area option 1 (acres)':[[10,.1],
                                      [6, 1],
                                      [3,10],
                                      [1,100],
                                      [0]],
                         'area option 2 (acres)':[[10,.05],
                                      [6, .5],
                                      [3,5],
                                      [1,50],
                                      [0]],
                         'area option 3 (acres)':[[10,.1],
                                      [6, .5],
                                      [3,1],
                                      [1,10],
                                      [0]]
                         }
        comparison_layers = {
                             'streets':{'location':streets,
                                        'breaks':vector_breaks},
                             'streams': {'location':streams,
                                         'breaks':vector_breaks},
                             'mines':{'location':mines,
                                        'breaks':vector_breaks},
                             'site_value':{'location':site_value, 
                                        'breaks':None},
                             'conspecifics':{'breaks':conspecific_breaks}
                             }
        #see above note when setting Multi_Factor_Site_Value variable
        if Multi_Factor_Site_Value:
            comparison_layers['partner_projects']={'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/priority_sites_Dissolve_Dice4",'breaks':vector_breaks}
            comparison_layers['t_and_e']={'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/T_E_2014_CCBasin_Dice",'breaks':vector_breaks}

        site_value_layer_described = arcpy.Describe(comparison_layers['site_value']['location'])

        
        #===============================================================================
        # get information on WHIPPET values
        #===============================================================================
        WHIPPET_scores = os.path.dirname(__file__) + "/species_scores.csv"
        with open(WHIPPET_scores,'rb') as file:
            contents = csv.reader(file)
            risk_scores={}
            for row in contents:
                if row[0] != "scientificname" and row[0] and row[1] == "TRUE":#column header and species defined
                    risk_scores[row[0]]=row[2:]
        
        if re_run == False:
            #===============================================================================
            # generate run location
            #===============================================================================
            timestring=str(int(time.time())).replace(" ", "_").replace("-", "_")
            
            Geodb_folder = os.path.dirname(__file__)  + "/results/" + timestring
            print "creating folder at " + Geodb_folder
            if not os.path.exists(Geodb_folder):
                os.makedirs(Geodb_folder)
                
            #===============================================================================
            # #copy run inputs and script into run directory
            #===============================================================================
            shutil.copyfile(WHIPPET_scores,Geodb_folder + "/"+ "WHIPPET_Scores.csv")
#             shutil.copy(os.path.dirname(__file__) + ,Geodb_folder + "/run_scipt" )
            
            #===========================================================================
            # create filegeodb
            #===========================================================================
            arcpy.CreateFileGDB_management(Geodb_folder,"Prioritize_the_WeedWise")
            out_gdb = Geodb_folder + "/Prioritize_the_WeedWise.gdb"
            
            #===========================================================================
            # copy prioritization layer into new geodb, filter out only relevant species records
            #===========================================================================
            arcpy.CopyFeatures_management(prioritization_layer,out_gdb+"/all_weed_points")
            sql = " OR ".join(map(lambda x: "\""+scientific_fieldname+"\" = '" + x + "'", risk_scores.keys()))
            arcpy.MakeFeatureLayer_management(out_gdb+"/all_weed_points", "weed_points2",sql)
            arcpy.CopyFeatures_management("weed_points2",out_gdb+"/target_weed_points")
            arcpy.CopyFeatures_management("weed_points2",out_gdb+"/target_weed_points_thinned") #not thinned yet, but will be
            prioritization_layer= out_gdb+"/target_weed_points_thinned"
            
            sr = arcpy.Describe(prioritization_layer).spatialReference
            prioritization_layer_linear_unit = sr.linearUnitName 
            if "Foot" == prioritization_layer_linear_unit:
                prioritization_layer_linear_unit = "feet"
                
            #print "using layer: " + prioritization_layer
            
            #===============================================================================
            # generate values
            #===============================================================================
            for layer in comparison_layers:
                print layer + "\n"
                if layer == 'conspecifics':
                    
                    #this logic reduces the density of points
                    arcpy.DeleteIdentical_management(prioritization_layer, ["Shape", scientific_fieldname], "33 Feet")
                    
                    #loop through species with WHIPPET scores, test if they are in dataset, setup layers for those that are
                    for risk_assessed in risk_scores:
                        risk_assessed_raw = risk_assessed
                        risk_assessed = risk_assessed.replace(" ","_")
                        risk_assessed = risk_assessed.replace(".","")
                        
                        print "checking " + risk_assessed_raw
                        arcpy.MakeFeatureLayer_management(prioritization_layer,risk_assessed, "\"" + scientific_fieldname + "\" = '"+risk_assessed_raw+"'","in_memory")
                        result = arcpy.GetCount_management(risk_assessed)
                        if int(result.getOutput(0)) >0:
                            calculate_scores(risk_assessed,risk_assessed, "conspecific", break_options[ comparison_layers[layer]['breaks']],get_conversion_num(prioritization_layer_linear_unit, comparison_layers[layer]['breaks'] ) )
                            print "        valid for this dataset\n"
                        else:
                            print "        not valid due to lack of points"
                        arcpy.Delete_management(risk_assessed)
                    continue
                else:
                    if layer == "site_value":
                        #TODO add test for RASTER vs. polygon and treat accordingly
                        if site_value_layer_described.dataType == "FeatureLayer":
                            #do an interseect to get attributes
                            arcpy.Intersect_analysis([comparison_layers[layer]['location'],prioritization_layer],prioritization_layer + "_withSiteValue")
                            
                        else: #raster dataset
                            # Check out the ArcGIS Spatial Analyst extension license
                            arcpy.CheckOutExtension("Spatial")
                            # Execute ExtractValuesToPoints
                            ExtractValuesToPoints(prioritization_layer, comparison_layers[layer]['location'], prioritization_layer + "_withSiteValue", "NONE", "ALL")
                            site_value_fieldname = "RASTERVALU"
                            
                            
                        arcpy.Delete_management(prioritization_layer)
                        prioritization_layer = prioritization_layer + "_withSiteValue"
                    else:    
                        # copy layer into new geodb
                        print "copying features\n"
                        arcpy.CopyFeatures_management(comparison_layers[layer]['location'],out_gdb+"/" + layer)
                    
                    if comparison_layers[layer]['breaks'] is not None:
                        print "calculating scores\n"
                    
                        #calculate scores
                        calculate_scores(prioritization_layer,out_gdb+"/" + layer,layer, break_options[comparison_layers[layer]['breaks']], get_conversion_num(prioritization_layer_linear_unit, comparison_layers[layer]['breaks'] ) )
        else:
            #use already calculated scores for faster testing of subsequent codebase
            prioritization_layer="" 
            out_gdb = ""
            Geodb_folder = ""
        
        
        weights = {
                'impact':.378,
                    'impact_to_wildlands':.483,
                    'site_value':.517,
                'invasiveness':.229,
                    'conspecifics':.378,
                    'rate_of_spread':.393,
                    'distance':.229,
                        'streets':.333,
                        'rivers':.425,
                        'mines':.243,
                'feasibility':.393,
                    'population_size':.253,
                    'reproductive_ability':.177,
                    'detectablility':.125,
                    'accessibility':.150,
                    'control_effectiveness':.190,
                    'control_cost':.105       
                 }   
        
        if Multi_Factor_Site_Value:
            #weight are used as percentages of score for site value
            weights['t_and_e']=.1
            weights['partner_projects']=.45
            weights['site_value2']=.45

        #===============================================================================
        # calculate population scores for each row
        #===============================================================================
#         print "calculating final scores"
        final_scores ={} #for reporting, below
        
        if re_run == False:
            arcpy.AddField_management(prioritization_layer,"WHIPPET_score_overall","FLOAT")
            arcpy.AddField_management(prioritization_layer,"WHIPPET_invasiveness_score","FLOAT")
            arcpy.AddField_management(prioritization_layer,"WHIPPET_feasibility_score","FLOAT")
            arcpy.AddField_management(prioritization_layer,"WHIPPET_impact_score","FLOAT")
        
        weeds = arcpy.UpdateCursor(prioritization_layer)
        
        for weed in weeds:
            if weed.isNull('conspecific_score'):
                continue
            if not Multi_Factor_Site_Value and weed.isNull(site_value_fieldname):
                #no valid site value score (-9999 is the null value for a the Extract Values to Points (used for Raster datasets)
                continue
            
            weed_name = weed.getValue(scientific_fieldname)
            if weed.isNull(patch_size_fieldname) or weed.getValue(patch_size_fieldname) == 0 or 1==0:
                population_score = default_population_score
            else:
                conversion_num = get_conversion_num(patch_size_unit, population_breaks)
                patch_size = weed.getValue(patch_size_fieldname)
                
#                 #===============================================================
#                 # #removed due this not being in the original algorithm
#                 #===============================================================
#                 if not weed.isNull(percent_cover_fieldname):
#                     patch_size = patch_size * (weed.getValue(percent_cover_fieldname)/100)
                
                population_score = score_using_breaks(patch_size,break_options[population_breaks],conversion_num)
            
            if weed.isNull(accessibility_fieldname):
                accessibility_score = default_accessibility_score
            else:
                accessibility_score = weed.getValue(accessibility_fieldname)
            
            #calculate site_value
            site_value_score = float(weed.getValue(site_value_fieldname))
            if site_value_score == -9999:
                site_value_score = 801
                #site_value_score = float(weed.getValue("RCS_HVH_rawscore"))
            
            #currently, raster site value data is expected to be normalized to 1000
            if not site_value_layer_described.dataType == "FeatureLayer":
                site_value_score = site_value_score/100
            
            #calculate multi-factor site value score using more than just site value information    
            if Multi_Factor_Site_Value:
                site_value_score = (weights['t_and_e'] * weed.getValue("t_and_e_score") + 
                                                     weights['site_value2'] * site_value_score +  
                                                     weights['partner_projects'] * weed.getValue("partner_projects_score"))
            
            impact_score =( weights['impact'] * ( weights['impact_to_wildlands'] * int(risk_scores[weed_name][1]) + 
                                              weights['site_value'] *  site_value_score  ))
            
            vector_score = vector_scored(risk_scores[weed_name],weights,{'streets':weed.getValue("streets_score"),'rivers':weed.getValue("streams_score"),'mines':weed.getValue("mines_score")})
            
            invasiveness_score = (weights['invasiveness'] *  ( weights['conspecifics'] * weed.getValue('conspecific_score') + 
                                                     weights['rate_of_spread'] * int(risk_scores[weed_name][3]) + 
                                                     weights['distance'] * vector_score ))
            
            
            feasibility_score =  (weights['feasibility'] *   (weights['population_size'] * population_score + 
                                                    weights['reproductive_ability'] * int(risk_scores[weed_name][5]) + 
                                                    weights['detectablility'] * int(risk_scores[weed_name][6]) + 
                                                    weights['accessibility'] * accessibility_score + 
                                                    weights['control_effectiveness'] * int(risk_scores[weed_name][8]) + 
                                                    weights['control_cost'] * int(risk_scores[weed_name][10])  )) 
    
            score = impact_score + invasiveness_score + feasibility_score
            
            if not weed_name in final_scores:  #setting up data structure for below report
                final_scores[weed_name]=[]
            final_scores[weed_name].append(score)
            
            weed.setValue("WHIPPET_score_overall",score)
            weed.setValue("WHIPPET_invasiveness_score",invasiveness_score)
            weed.setValue("WHIPPET_feasibility_score",feasibility_score)
            weed.setValue("WHIPPET_impact_score",impact_score)
            weeds.updateRow(weed)
        
        
        #defining derived output layer
        parameters[13].value = prioritization_layer
         
        #===============================================================================
        # develop charts
        #===============================================================================
        print "making charts\n"
        
        medians={}
        text = ""
        all = []
        replacements = []
        
        def myround(x,prec=2,base=.25):
            return round(base * round(float(x)/base),prec)
        
        for weed in final_scores:
            a = np.array( final_scores[weed])
            medians[np.percentile(a, 50)]=  weed
             
        for median in sorted(medians.keys()):
            weed = medians[median]
            
            a = np.around(np.array( final_scores[weed]),3)
            
            all.extend(final_scores[weed])
            text = text + "['"+weed+"', " + str(np.min(a)) + ","+ str(np.percentile(a, 25)) +","+ str(np.percentile(a, 75)) + ","+ str(np.max(a)) +"],\n"
            
        replacements.append(["//edit content - box","//edit content - box\n" + text])
        
        text = ""
        all = sorted(map(myround,all))
        for item in np.arange(all[0],all[-1],0.25):
            text = text + "["+str(item)+","+str(all.count(item))+"],\n"
        
        replacements.append(["//edit content - overall priority","//edit content - overall priority\n" + text])
        edit_report ("whippet_chart",Geodb_folder, replacements)


if __name__ == '__main__':
    # This is used for debugging. Using this structure makes it much easier to debug using standard Python development tools.

    #switch this to a True case if you are running in debug mode, you have to switch back to a False case when loading into arcmap otherwise it will run when arcmap loads the toolbox.
    if 1==1:
        tasks = Whippet()
        params = tasks.getParameterInfo()
        #make feature layer
        #arcpy.MakeFeatureLayer_management("G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/CRISP_Weed_Observations_OregonSP","weed_point_layer")
        arcpy.MakeFeatureLayer_management("G:/Projects/CRISP_Fall2015Update/Data/WHIPPET_Data/CRISP_Fall2015_Update.gdb/New_Data_Test1_SP_SiteValue2","weed_point_layer")
        params[0].value = "weed_point_layer" #layer to process
        params[1].value = 'scientificname'  
        params[2].value = 'obsPatchSize'  
        params[3].value = "digitalPhoto5"#just using an attribute with all null values for testing "accessibility_score"
        params[4].value = "square feet"
        params[5].value = 'conspecifics option 2 (miles)'
        params[6].value = 'area option 2 (acres)'

        #make feature layer
#         arcpy.MakeFeatureLayer_management("G:/Projects/CRISP/Whippet Support/New File Geodatabase.gdb/dummy_site_value","dummy_site_value")
        arcpy.MakeRasterLayer_management ("G:/Projects/CRISP_Fall2015Update/Data/WHIPPET_Data/CRISP_Fall2015_Update.gdb/HVH", "site_value_raster")
        params[7].value = "site_value_raster"
        params[8].value = "Value"
        
        #make feature layer
        arcpy.MakeFeatureLayer_management("G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_mc_streams","streams")
        params[9].value = "streams"
        #make feature layer
        arcpy.MakeFeatureLayer_management("G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_basin_streets","streets")
        params[10].value = "streets"
        #make feature layer
        arcpy.MakeFeatureLayer_management("G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_basin_mines","mines")
        params[11].value = "mines"
        
        params[12].value = 'distance option 2 (miles)'
        
        tasks.execute(params, None)
        

        print(tasks.label)
    else:
        pass
    
    pass
