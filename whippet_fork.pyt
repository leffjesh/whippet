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
'''
import arcpy
import time
import datetime
import csv
import os
import inspect
import shutil
import numpy as np

def edit_report(report_name, output_dir, replacements, new_report_name=None):
    f = open(report_templates + "/" + report_name + ".html")
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

def score_using_breaks (value, breaks):
    #TODO: order breaks automatically to ensure structure
    for criteria in breaks:
        if len(criteria)==1:#last option
            return criteria[0]
        if value < criteria[1]:
            return criteria[0]
    return False

def vector_scored (risk_scores,weights,values):
    # vector scores are only valid if this species is affect by the associated vector
    # here we are re-calculating the weights based on what vectors are valid for this species.
    #    e.g. if rivers are the only valid vector then don't weight it, just return that score
    # I'm not sure if this methodology is valid or if we should just ignore scores with when a given vector is invalid (i.e. set that vector score to 0)
    
    score = 0
    vectors = []
    if risk_scores[11] == "yes":
        vectors.append("streets")
    if risk_scores[12] == "yes":
        vectors.append("rivers")
    if risk_scores[13] == "yes":
        vectors.append("mines")
    
    total = sum(map(lambda x: weights[x], vectors))
    
    for vector in vectors:
        weights[vector]=weights[vector]/total
        score = score + weights[vector] * values[vector]
    
    return score

def calculate_scores(source_layer, target_layer,layer_name,breaks):
    try:
        arcpy.Near_analysis(source_layer,target_layer)
        arcpy.AddField_management(source_layer,layer_name+"_score","SHORT")
        arcpy.DeleteField_management (source_layer,"NEAR_FID")
        
        weeds = arcpy.UpdateCursor(source_layer)
        for weed in weeds:
            weed.setValue(layer_name+"_score",score_using_breaks(weed.getValue("NEAR_DIST"), breaks) )
            weeds.updateRow(weed)
        
        arcpy.DeleteField_management (source_layer,"NEAR_DIST")
        del weed, weeds
        
    except:
        print arcpy.GetMessages()
        
class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Whippet_python"
        self.alias = ""
        # List of tool classes associated with this toolbox
        self.tools = [Whippet_python]
        
        
class Whippet_python(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Whippet_python"
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
            displayName="Scientific Name",
            name="Scientific",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        
        param2 = arcpy.Parameter(
            displayName="Scoring table",
            name="WHIPPET_Scores",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="streams",
            name="streams_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        param4 = arcpy.Parameter(
            displayName="streets",
            name="streets_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        param0.filter.list = ["Point"]
        param3.filter.list = ["Polyline"]
        param4.filter.list = ["Polyline"]
        
        params = [param0, param1, param2,param3,param4]
    
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
        bulk_in_sci_field = parameters[1].value
        WHIPPET_scores = parameters[2].value
        streams = parameters[3].value
        streets = parameters[4].value
        mines = parameters[5].value
        vector_breaks = parameters[6].value
        
        run_location= "G:/Projects/CRISP/Dataset_Analysis/CRISP_Runs"
        #prioritization_layer = "G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/CRISP_Weed_Observations_OregonSP"
        #WHIPPET_scores = "G:/Projects/CRISP/Whippet Support/species_scores.csv"
        re_run = False
        report_templates = "G:/Projects/CRISP/Whippet Support/"

        break_options = {'coarse (miles)':[[10,.1],
                                   [6,1],
                                   [3,10],
                                   [1,25],
                                   [0]],
                         'semi-coarse (miles)':[[10,.01],
                                   [6,.1],
                                   [3,1],
                                   [1,5],
                                   [0]],
                         'semi-fine (miles)':[[10,.01],
                                   [6,.05],
                                   [3,.1],
                                   [1,1],
                                   [0]],
                         'fine (miles)':[[10,.001],
                                   [6,.01],
                                   [3,.1],
                                   [1,1],
                                   [0]],
                         'coarse (acres)':[[10,.1],
                                      [6, 1],
                                      [3,10],
                                      [1,100],
                                      [0]],
                         'fine (acres)':[[10,.1],
                                      [6, .5],
                                      [3,1],
                                      [1,10],
                                      [0]]
                         }
#        rivers previously;;;;;;;;;;;;;;;;;;;;;;;;; [[10,520], #if less than 528 ft, use value 10
#                                                   [6,1560],#else if less than 5280 use 6
#                                                   [3,3120], #else if less than 52800 use 3
#                                                   [1,5280], #else if less than 132000 use 1
#                                                   [0]] #greater than previous number use value 0
        comparison_layers = {
                             'streets':{'location':streets,
                                        'breaks':'semi-fine (miles)'},
                             'population_size':{
                                        'breaks':'fine (acres)'
                                        },
                             'partner_projects':{
                                        'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/priority_sites_Dissolve_Dice4", 
                                        'breaks':'semi-fine (miles)'
                                        },
                             'priority_sites':{
                                        'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/jason_priority_sites",
                                        'breaks':'semi-fine (miles)'
                                        },
                             't_and_e':{
                                        'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/T_E_2014_CCBasin_Dice",
                                        'breaks':'semi-fine (miles)'
                                        },
                             'oaks':{
                                        'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/oaks",
                                        'breaks':'semi-fine (miles)'
                                        },
                             'streams':{
                                        'location':streams,#"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_mc_streams",#"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/major_streams",#'F:\hydrography\RLIS_riv_line.shp',#
                                        'breaks':'semi-fine (miles)'

                                        },
                             'conspecifics':{'breaks':'semi-fine (miles)'
                                            },
                             }
        
        #===============================================================================
        # get information on WHIPPET values
        #===============================================================================
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
            
            Geodb_folder = run_location + "/" + timestring
            print "creating folder at " + Geodb_folder
            if not os.path.exists(Geodb_folder):
                os.makedirs(Geodb_folder)
                
            #===============================================================================
            # #copy script into run directory
            #===============================================================================
            shutil.copyfile(inspect.stack()[0][1],Geodb_folder + "\\"+ os.path.basename(inspect.stack()[0][1]))
            shutil.copyfile(WHIPPET_scores,Geodb_folder + "\\"+ "WHIPPET_Scores.csv")
        
            #===========================================================================
            # create filegeodb
            #===========================================================================
            
            arcpy.CreateFileGDB_management(Geodb_folder,"Prioritize_the_WeedWise")
            out_gdb = Geodb_folder + "/Prioritize_the_WeedWise.gdb"
            
            
            #===========================================================================
            # copy prioritization layer into new geodb, filter out only relevant species records
            #===========================================================================
            arcpy.CopyFeatures_management(prioritization_layer,out_gdb+"/weed_points_orig")
            sql = " OR ".join(map(lambda x: "\"scientificname\" = '" + x + "'", risk_scores.keys()))
            arcpy.MakeFeatureLayer_management(out_gdb+"/weed_points_orig", "weed_points2",sql)
        #     arcpy.SelectLayerByAttribute_management("weed_points2","NEW_SELECTION",sql)
        #     result = arcpy.GetCount_management("weed_points2")
        #     if int(result.getOutput(0)) >0:
        #         print "success"
            arcpy.CopyFeatures_management("weed_points2",out_gdb+"/weed_points")
            prioritization_layer= out_gdb+"/weed_points"
            print "using layer: " + prioritization_layer
            
            
            #===============================================================================
            # generate values
            #===============================================================================
        
            for layer in comparison_layers:
                print layer + "\n"
                if layer == 'conspecifics':
                    arcpy.DeleteIdentical_management(prioritization_layer, ["Shape", "scientificname"], "33 Feet")
                    
                    #loop through species with WHIPPET scores, test if they are in dataset, setup layers for those that are
                    for risk_assessed in risk_scores:
                        risk_assessed_raw = risk_assessed
                        risk_assessed = risk_assessed.replace(" ","_")
                        risk_assessed = risk_assessed.replace(".","")
                        
                        print "checking " + risk_assessed_raw
                        arcpy.MakeFeatureLayer_management(prioritization_layer,risk_assessed, "\"scientificname\" = '"+risk_assessed_raw+"'","in_memory")
                        result = arcpy.GetCount_management(risk_assessed)
                        if int(result.getOutput(0)) >0:
                            calculate_scores(risk_assessed,risk_assessed,risk_assessed, comparison_layers[layer]['breaks'])
                            print "        valid for this dataset\n"
                        else:
                            print "        not valid due to lack of points"
                        arcpy.Delete_management(risk_assessed)
                    continue
                elif layer == 'population_size':
                    continue
                else:
                    print "copying features\n"
                    
                    # copy layer into new geodb
                    arcpy.CopyFeatures_management(comparison_layers[layer]['location'],out_gdb+"/" + layer)
                    
                    print "calculating scores\n"
                    
                    #calculate scores
                    calculate_scores(prioritization_layer,out_gdb+"/" + layer,layer, break_options[vector_breaks] )
        else:
            #use already calculated scores for faster testing of subsequent codebase
            prioritization_layer="G:/Projects/CRISP/Dataset_Analysis/CRISP_Runs/1423696819/Prioritize_the_WeedWise.gdb/weed_points" 
            out_gdb = "G:/Projects/CRISP/Dataset_Analysis/CRISP_Runs/1423696819/Prioritize_the_WeedWise.gdb"
            Geodb_folder = "G:/Projects/CRISP/Dataset_Analysis/CRISP_Runs/1423696819"
        
        
        weights = {
                'impact':.378,
                    'impact_to_wildlands':.483,
                    'site_value':.517,
                        'oaks':.2,
                        't_and_e':.2,
                        'partner_projects':.25,
                        'priority_sites':.35,
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
        #===============================================================================
        # calculate population scores for each row
        #===============================================================================
        
            
        print "calculating final scores"
        
        final_scores ={}
        
        if re_run == False:
            arcpy.AddField_management(prioritization_layer,"WHIPPET_score_overall","FLOAT")
            arcpy.AddField_management(prioritization_layer,"WHIPPET_invasiveness_score","FLOAT")
            arcpy.AddField_management(prioritization_layer,"WHIPPET_feasibility_score","FLOAT")
            arcpy.AddField_management(prioritization_layer,"WHIPPET_impact_score","FLOAT")
        
        fields = []
        fieldList = arcpy.ListFields(prioritization_layer)
        for field in fieldList:
            fields.append(field.name)
            
        weeds = arcpy.UpdateCursor(prioritization_layer)
        
        for weed in weeds:
            conspecific_score = weed.getValue("scientificname")
            conspecific_score = conspecific_score.replace(" ","_")
            conspecific_score = conspecific_score.replace(".","") + "_score"
        #     print weed.getValue("OBJECTID")
            
            if  conspecific_score in fields:
                if weed.isNull(conspecific_score):
                    continue
                
                weed_name = weed.getValue("scientificname")
                if weed.isNull("obsPatchSize"):
                    population_size = 3
                else:
                    population_size = score_using_breaks(weed.getValue("obsPatchSize"),comparison_layers['population_size']['breaks'])
                    
                
                impact_score =( weights['impact'] * ( weights['impact_to_wildlands'] * int(risk_scores[weed_name][1]) + 
                                                  weights['site_value'] *(   weights['oaks'] * weed.getValue("oaks_score") + 
                                                                             weights['t_and_e'] * weed.getValue("t_and_e_score") + 
                                                                             weights['priority_sites'] * weed.getValue("priority_sites_score") + 
                                                                             weights['partner_projects'] * weed.getValue("partner_projects_score") ))) 
                
                #is this valid, or is the simpler option better?
                vector_score= vector_scored(risk_scores[weed_name],weights,{'streets':weed.getValue("streets_score"),'rivers':weed.getValue("streams_score"),'mines':3.0})
                
                invasiveness_score = (weights['invasiveness'] *  ( weights['conspecifics'] * weed.getValue(conspecific_score) + 
                                                         weights['rate_of_spread'] * int(risk_scores[weed_name][3]) + 
                                                         weights['distance'] * vector_score ))
                
                
                feasibility_score =  (weights['feasibility'] *   (weights['population_size'] * population_size + 
                                                        weights['reproductive_ability'] * int(risk_scores[weed_name][5]) + 
                                                        weights['detectablility'] * int(risk_scores[weed_name][6]) + 
                                                        weights['accessibility'] * 3 + 
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
    # This is used for debugging. Using this separated structure makes it much easier to debug using standard Python development tools.

    if 1==1:
        tasks = Whippet_python()
        params = tasks.getParameterInfo()
        params[0].value = "G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/CRISP_Weed_Observations_OregonSP"  #layer to process
        params[1].value = 'scientific'  #attribute for scientific name in above layer
        params[2].value = "G:/Projects/CRISP/Whippet Support/species_scores.csv"
        params[3].value = "G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_mc_streams"
        params[4].value = "G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_basin_streets"
        
        tasks.execute(params, None)

        print(tasks.label)
    else:
        pass
    
    pass
