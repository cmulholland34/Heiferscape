import pandas as pd
import csv

class Pasture_Heifer_Balance:
    # AOI = [ acreage, type of conversion]
    # Step 1
    def __init__(self, AOI_1 = [0,0] , AOI_2 = [0,0], AOI_3 = [0,0]):
        self.nutrients = pd.read_csv("nutrients.csv")
        self.NRC = pd.read_csv("NRC_2001.csv")
        self.pasture = pd.read_excel("pasture_prediction.xls")
        self.AOI_1 = AOI_1
        self.AOI_2 = AOI_2
        self.AOI_3 = AOI_3
        self.AOI_list = [AOI_1, AOI_2, AOI_3]
        self.acreage = self.AOI_1[0] + self.AOI_2[0] + self.AOI_3[0]
     
    def pasture_utilization(self,occupancy,species_list, target_residual):
        # Step 4
        # species_list = [AOI_1 species, AOI_2 species, AOI_3 species] 
        # species must be a string of one of the following ["Low Yielding Variety","Medium Yielding Variety","High Yielding Variety"]
        # occupancy must be a string of one of the follwoing ["<1 day", "1 day", "3 days", "7 days", "Continuous"]
        #target residual must be float that represents the amount of pasture left to be residual. EX: 50% target resiudal would be entered as 0.5
        yields = self.pasture[self.pasture["Occupancy"] == occupancy]
        weighted_average = 0
        for i in range(len(species_list)):
            prediction = list(yields[species_list[i]])[i]
            weighted_value = (self.AOI_list[i][0]/self.acreage)*prediction
            weighted_average += weighted_value
        pasture_utilization = (weighted_average*(1-target_residual))*self.acreage
        # pasture_utilization is a prediction of the annual tons of dry matter yield from all of the AOIs
        headers = ["name","unit","figure"]
        utilization_row = ["pasture_utilization","Tons of DM/season",pasture_utilization]
        with open("working.csv", "w") as f:
            write = csv.writer(f)
            write.writerow(headers)
            write.writerow(utilization_row)
        return(["Available Tons of Dry Matter off pasture during the grazing season",pasture_utilization])
            
    def pasture_sufficiency(self, numb_heifer, breed, bred, avg_initial_weight, target_daily_gain, days_on_pasture, outside_feed = None):
        #Step 5
        # target_daily_gain must be a float  [0.7,0.9,1.1,1.3,1.5,1.8,2.0,2.2]
        # breed must be a string ["small","large"]
        # bred must be a string ["bred", "non bred"]
        # outside_feed is the percentage of feed ration the user plans to supplement with other feedsources. Must be 10% or higher for a calcuable impact. 
        field_names = self.nutrients.columns.tolist()
        working_data = pd.read_csv("working.csv")
        pasture_utilization = working_data[working_data["name"] == "pasture_utilization"]["figure"].tolist()[0]
        avg_weight = (avg_initial_weight + (avg_initial_weight + target_daily_gain*days_on_pasture))/2
        nrc = self.NRC[self.NRC["Breed"]==breed]
        nrc_x= nrc[nrc["Bred"]==bred]
        nrc_data = nrc_x[nrc_x["ADG"]== str(target_daily_gain)]
        heifer = pd.concat([nrc_data[nrc_data["BW"] < str(avg_weight)].tail(1)])
        # DMI_Per_Season is the Tons of Dry Matter the herd will eat in a season
        DMI_Per_Season = (eval(heifer["DMI"].tolist()[0])*numb_heifer*days_on_pasture)/2000
        if (float(pasture_utilization)/DMI_Per_Season > 1.3):
            return("EXCESS FORAGE AVAILABLE FOR HERD: Either increase herd size, increase target daily gain, or rerun previous function")
        if (float(pasture_utilization)/DMI_Per_Season >= 1.2 and float(pasture_utilization)/DMI_Per_Season <= 1.30):
            with open("working.csv","a") as f:
                write = csv.writer(f)
                write.writerow(["Pasture Dry Matter Demand", "Tons of DM/seson",DMI_Per_Season])
                write.writerow(["Pasture DMI Percentage","%",100])
            with open("nutrient_rec.csv","w") as file:
                writer = csv.writer(file)
                writer.writerow(field_names)
                writer.writerow(["Nutrient_Recommendation"]+ heifer.values.tolist()[0][4:])
            return("SUFFICIENT FORAGE AVAILABLE FOR HERD: Continue on")
        if (float(pasture_utilization)/DMI_Per_Season < 1.2 and outside_feed < 10):
            return("INSUFFICIENT FORAGE AVAILABLE FOR HERD: Reduce herd size, reduce target daily gain, rerun previous function, or increase outside feedsources")
        if (float(pasture_utilization)/DMI_Per_Season < 1.2 and outside_feed > 10):
            if (float(pasture_utilization)/(DMI_Per_Season - DMI_Per_Season*(outside_feed/100)) < 1.2):
                return("INSUFFICIENT FORAGE AVAILABLE FOR HERD: Reduce herd size, reduce target daily gain, rerun previous function, or increase outside feedsources")
            if (float(pasture_utilization)/(DMI_Per_Season - DMI_Per_Season*(outside_feed/100)) >= 1.2 and float(pasture_utilization)/(DMI_Per_Season - DMI_Per_Season*(outside_feed/100)) <= 1.3):
                with open("nutrient_rec.csv","w") as c:
                    writer = csv.write(c)
                    writer.writerow(field_names)
                    writer.writerow(["Nutrient_Recommendation"]+ heifer.values.tolist()[0][4:])
                with open("working.csv","a") as d:
                    write = csv.writer(d)
                    write.writerow(["Pasture Dry Matter Demand", "Tons of DM/seson",DMI_Per_Season - DMI_Per_Season*(outside_feed/100)])
                    write.writerow(["Pasture DMI Percentage", "%",(100-outside_feed)])
                return("SUFFICIENT FORAGE AVAILABLE FOR HERD: Continue on")
            else:
                return("EXCESS FORAGE AVAILABLE FOR HERD: Either increase herd size, decrease outside feed %, increase target daily gain, or rerun previous function")
        
        
       
        
class Pasture_Feeding_Plan:
    
    def __init__(self):
        self.NRC = pd.read_csv("NRC_2001.csv")
        self.nutrients = pd.read_csv("nutrients.csv")
        self.nutrient_rec = pd.read_csv("nutrient_rec.csv")
        self.working = pd.read_csv("working.csv")
        
        
    def pasture_feeding_plan(self,TMR_Nutrient_Profile = None, TMR_DMI_Percentage=None, DMI_list = None):
        # TMR_Nutrient_Profile must be a list of the nutrients of the user's TMR they use. [% of DM, TDN (%), NEm (Mcal/lb), NEg (Mcal/lb), ME (Mcal/lb), RDP (% of CPa), RUP (% of CPa), CPa (% of DM), Ca (% of DM), P (% of DM)]
        # TMR_DMI_Percentage is the percentage of the dry matter intake that the user designates to use their TMR. Must input one if user inputs a nutrient profile
        # If the user inputs a TMR_Nutrient_Profile it is asummed that will make up the total non-pasture formulation
        # DMI_list is a list of floats of percentages the user will designate for the folowing feed sources [Barley, Ground Corn, Corn Silage, Hay, Soybean, Wheat] EX: [0,0,.2,0,0,0]
        pasture_dmi_perc = (self.working[self.working["name"]=="Pasture DMI Percentage"]["figure"].tolist()[0])/100
        NRC_Rec = self.nutrient_rec[self.nutrient_rec["name"] == "Nutrient_Recommendation"].values.tolist()[0][1:]
        if (TMR_Nutrient_Profile != None):
            TMR_nutrients = [x*(TMR_DMI_Percentage/100) for x in TMR_Nutrient_Profile]
            pasture_nutrients = [n*(1 -(TMR_DMI_Percentage/100)) for n in self.nutrients[self.nutrients["name"] == "MMG Pasture"].values.tolist()[0][1:]]
            feed_nutrient_profile = [c+d for (c,d) in zip(TMR_nutrients, pasture_nutrients)]
            if ( float(feed_nutrient_profile[1]) < float(NRC_Rec[1])):
                return("TDN % TOO LOW: Your heifer herd will not meet average daily gain goal due to lack of digestable energy, supplement with high energy feed, or lower average daily gain expectations in previous function.")
            if (float(feed_nutrient_profile[1]) >= float(NRC_Rec[1]) and float(feed_nutrient_profile[2])*float(NRC_Rec[0]) >= float(NRC_Rec[2]) and float(feed_nutrient_profile[3])*float(NRC_Rec[0]) >= float(NRC_Rec[3]) and float(feed_nutrient_profile[4])*float(NRC_Rec[0]) >= float(DMI_Rec[4]) ):
                with open("nutrients.csv","a") as f:
                    write = csv.writer
                    write.writerow(["Feeding plan nutrient profile"] + feed_nutrient_profile)
                return("FEEDING PLAN IS NUTRIENT SUFFICENT: Continue on")
            else :
                return("FEEDING PLAN IS ENERGY DEFICIENT: Atleast one of the energy figures (NEm,NEg,ME) is below the NRC recommendation, supplement with high energy feed, or lower average daily gain expectations in previous function")
        if (TMR_Nutrient_Profile == None):
            pasture_nutrients = [x*pasture_dmi_perc for x in self.nutrients[self.nutrients["name"] == "MMG Pasture"].values.tolist()[0][1:]]
            other_feeds = self.nutrients.drop(columns = ['name'], index = self.nutrients.index[0])
            outside_feed = other_feeds.astype(float)
            outside = outside_feed.mul(DMI_list, axis = 0)
            other_feed_nutrients = outside.sum(axis=0).tolist()
            feed_nutrient_profile = [x+y for (x,y) in zip(other_feed_nutrients, pasture_nutrients)]
            if ( float(feed_nutrient_profile[1]) < float(NRC_Rec[1])):
                return("TDN % TOO LOW: Your heifer herd will not meet average daily gain goal due to lack of digestable energy, supplement with high energy feed, or lower average daily gain expectations in previous function.")
            if (float(feed_nutrient_profile[1]) >= float(NRC_Rec[1]) and float(feed_nutrient_profile[2])*float(NRC_Rec[0]) >= float(NRC_Rec[2]) and float(feed_nutrient_profile[3])*float(NRC_Rec[0]) >= float(NRC_Rec[3]) and float(feed_nutrient_profile[4])*float(NRC_Rec[0]) >= float(NRC_Rec[4])):
                with open("nutrients.csv","a") as f:
                    write = csv.writer
                    write.writerow(["Feeding plan nutrient profile"] + feed_nutrient_profile)
                return("FEEDING PLAN IS NUTRIENT SUFFICENT: Continue on")
            else :
                return("FEEDING PLAN IS ENERGY DEFICIENT: Atleast one of the energy figures (NEm,NEg,ME) is below the NRC recommendation, supplement with high energy feed, or lower average daily gain expectations in previous function") 
                                 
                
                
           
            
        
        

        
#class Pasture_Setup_Operating_Cost:
    
#    def __init__(self):
        

#class Existing_Heifer_Raising:
    
#    def __init__(self):
        
    
    
#class Financial_Analysis:
    
 #   def __init__(self):
        