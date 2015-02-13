import arcpy, time,datetime,csv,os,inspect, shutil
import numpy as np

run_location= "G:/Projects/CRISP/Dataset_Analysis/CRISP_Runs"
prioritization_layer = "G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/CRISP_Weed_Observations_OregonSP"
WHIPPET_scores = "G:/Projects/CRISP/Whippet Support/species_scores.csv"
projection = prioritization_layer
re_run = True
report_templates = "G:/Projects/CRISP/Whippet Support/"

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
    if risk_scores[weed_name][11] == "yes":
        vectors.append("streets")
    if risk_scores[weed_name][12] == "yes":
        vectors.append("rivers")
    if risk_scores[weed_name][13] == "yes":
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

comparison_layers = {
                     'streets':{
                                'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_basin_streets",#"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/major_roads", #
                                'units':"feet",
                                'breaks':[[10,52], #if less than 528 ft, use value 10
                                          [6,265],#else if less than 5280 use 6
                                          [3,528], #else if less than 52800 use 3
                                          [1,5280], #else if less than 132000 use 1
                                          [0]] #greater than previous number, less then this number
                                },
                     'population_size':{
                                'units':"feet",
                                'breaks':[[10,4356], #if less than 528 ft, use value 10
                                          [6,21780],#else if less than 5280 use 6
                                          [3,43560], #else if less than 52800 use 3
                                          [1,435600], #else if less than 132000 use 1
                                          [0]] #greater than previous number, less then this number
                                },
                     'partner_projects':{
                                'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/priority_sites_Dissolve_Dice2", #"F:/transportation/CC_Streets.shp",
                                'units':"feet",
                                'breaks':[[10,52],
                                          [6,528],
                                          [3,2640],
                                          [1,5280],
                                          [0]] #greater than previous number, less then this number
                                },
                     'priority_sites':{
                                'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/jason_priority_sites",
                                'units':"feet",
                                'breaks':[[10,52],
                                          [6,528],
                                          [3,2640],
                                          [1,5280],
                                          [0]] #greater than previous number, less then this number
                                },
                     't_and_e':{
                                'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/T_E_2014_CCBasin_Dice",
                                'units':"feet",
                                'breaks':[[10,52],
                                          [6,528],
                                          [3,2640],
                                          [1,5280],
                                          [0]] #greater than previous number, less then this number
                                },
                     'oaks':{
                                'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/oaks",
                                'units':"feet",
                                'breaks':[[10,52],
                                          [6,528],
                                          [3,2640],
                                          [1,5280],
                                          [0]] #greater than previous number, less then this number
                                },
                     'streams':{
                                'location':"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/cc_mc_streams",#"G:/Projects/CRISP/Dataset_Analysis/WeedData_ClackamasBasin.mdb/major_streams",#'F:\hydrography\RLIS_riv_line.shp',#
                                'units':"feet",
                                'breaks':[[10,520], #if less than 528 ft, use value 10
                                          [6,1560],#else if less than 5280 use 6
                                          [3,3120], #else if less than 52800 use 3
                                          [1,5280], #else if less than 132000 use 1
                                          [0]] #greater than previous number use value 0
                                },
                     'conspecifics':{
                                    'units':"feet",
                                    'breaks':[[0,528], #if less than 528 ft, use value 0
                                              [1,1584],#else if less than 5280 use 1
                                              [3,5280], #else if less than 52800 use 3
                                              [6,26400], #else if less than 132000 use 6
                                              [10]], #greater than previous number use value 10
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
            calculate_scores(prioritization_layer,out_gdb+"/" + layer,layer, comparison_layers[layer]['breaks'])
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
        vector_score= vector_scored(risk_scores,weights,{'streets':weed.getValue("streets_score"),'rivers':weed.getValue("streams_score"),'mines':3.0})
        
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

# #===============================================================================
# # setup mxd
# #===============================================================================
# print "setting up mxd..."
# 
# mxd = "G:/Projects/CRISP/Dataset_Analysis/CRISP2014_template.mxd"
# shutil.copyfile(mxd,Geodb_folder+"/good_to_go.mxd")
# mxd = Geodb_folder+"/good_to_go.mxd"
# 
# arcpy.env.workspace = out_gdb
# # Set overwrite option
# arcpy.env.overwriteOutput = True
# my_mxd = arcpy.mapping.MapDocument(mxd)  
# data_frame = arcpy.mapping.ListDataFrames(my_mxd)[0]  
# # Switch to data view  
# my_mxd.activeView = data_frame.name  
# 
# for comparison_layer in comparison_layers:
#     if comparison_layer == "conspecifics":
#         comparison_layer = "weed_points"
#     elif comparison_layer == "population_size":
#         continue
#         
#     arcpy.MakeFeatureLayer_management( comparison_layer ,comparison_layer + "_lyr")
#     addLayer=arcpy.mapping.Layer(comparison_layer + "_lyr")
#     addLayer.name=comparison_layer + " layer"
#     
#     arcpy.mapping.AddLayer(data_frame,addLayer)
# my_mxd.save()
# del my_mxd

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
