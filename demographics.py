import pandas as pd
import censusdata

# DOWNLOAD DATA
# Data extracts using CensusData API package
# Most vars: 2015 ACS 5-year estimates
acs = censusdata.download("acs5", 2015, censusdata.censusgeo([("county", "*")]),
    ["STATE", "COUNTY",    #the basics
    "B05001_001E", "B05001_005E", "B05001_006E",    #citizenship
    "B16002_001E", "B16002_004E", "B16002_007E", "B16002_010E", "B16002_013E",    #limited english
    "B15002_001E", "B15002_003E", "B15002_004E", "B15002_005E", "B15002_006E", 
    "B15002_007E", "B15002_008E", "B15002_009E", "B15002_010E", "B15002_011E",
    "B15002_020E", "B15002_021E", "B15002_022E", "B15002_023E", "B15002_024E", 
    "B15002_025E", "B15002_026E", "B15002_027E", "B15002_028E",                   #ed attainment
    "B17001_001E", "B17001_002E",    #poverty level
    "B25064_001E",    #median rent
    "B27001_001E", "B27001_005E", "B27001_008E", "B27001_011E", "B27001_014E", 
    "B27001_017E", "B27001_020E", "B27001_023E", "B27001_026E", "B27001_029E",
    "B27001_033E", "B27001_036E", "B27001_039E", "B27001_042E", "B27001_045E", 
    "B27001_048E", "B27001_051E", "B27001_054E", "B27001_057E"                    #health insurance
    ])

# Race vars: 2010 Decennial Census summary file
census = censusdata.download("sf1", 2010, censusdata.censusgeo([("county", "*")]),
    ["STATE", "COUNTY",    #the basics
    "P008001",    #total pop
    "P008003",    # White alone
    "P008004",    # Black or African American alone
    "P008005",    # American Indian and Alaska Native alone
    "P008006",    # Asian alone
    "P008007",    # Native Hawaiian and Other Pacific Islander alone
    "P008008"     # Some Other Race alone
    ])


# CREATE VARS

# ACS (demos)
acs_demos = pd.DataFrame()
acs_demos["state"] = acs["STATE"]
acs_demos["county"] = acs["COUNTY"]

# Percent of US citizens that are citizens by naturalization
acs_demos["pct_p_citizens_bynat"] = acs["B05001_005E"] / (acs["B05001_001E"] - 
                                                                    acs["B05001_006E"])

# Percent of households with limited English proficiency
acs_demos["pct_h_lep"] = (acs["B16002_004E"] + acs["B16002_007E"] + 
                        acs["B16002_010E"] + acs["B16002_013E"]) / acs["B16002_001E"]

# Percent of individuals with highest education attainment HS degree or lower
edvars_men = ["B15002_003E", "B15002_004E", "B15002_005E", "B15002_006E", "B15002_007E", 
                "B15002_008E", "B15002_009E", "B15002_010E", "B15002_011E"]
edvars_women = ["B15002_020E", "B15002_021E", "B15002_022E", "B15002_023E", "B15002_024E", 
                "B15002_025E", "B15002_026E", "B15002_027E", "B15002_028E"]
acs_demos["pct_p_hs_orless"] = 0
for var in edvars_men + edvars_women:
    acs_demos["pct_p_hs_orless"] += acs[var]
acs_demos["pct_p_hs_orless"] = acs_demos["pct_p_hs_orless"] / acs["B15002_001E"]

# Percent of households below poverty level
acs_demos["pct_p_below_poverty"] = acs["B17001_002E"] / acs["B17001_001E"]

# Households' median rent 
acs_demos["gross_hh_rent"] = acs["B25064_001E"]

# Percent with health insurance coverage 
insvars_men = ["B27001_005E", "B27001_008E", "B27001_011E", "B27001_014E", "B27001_017E", 
                "B27001_020E", "B27001_023E", "B27001_026E", "B27001_029E"]
insvars_women = ["B27001_033E", "B27001_036E", "B27001_039E", "B27001_042E", "B27001_045E", 
                "B27001_048E", "B27001_051E", "B27001_054E", "B27001_057E"]
acs_demos["pct_p_no_insurance"] = 0
for var in insvars_men + insvars_women:
    acs_demos["pct_p_no_insurance"] += acs[var]
acs_demos["pct_p_no_insurance"] = acs_demos["pct_p_no_insurance"] / acs["B27001_001E"]


# CENSUS (race)
census_demos = pd.DataFrame()
census_demos["state"] = census["STATE"]
census_demos["county"] = census["COUNTY"]

# Percent White
census_demos["pct_p_white"] = census["P008003"] / census["P008001"]

# Percent Black or African American
census_demos["pct_p_black"] = census["P008004"] / census["P008001"]

# Percent American Indian and Alaska Native
census_demos["pct_p_native"] = census["P008005"] / census["P008001"]

# Percent Asian
census_demos["pct_p_asian"] = census["P008006"] / census["P008001"]

# Percent Native Hawaiian and other Pacific Islander
census_demos["pct_p_pacific"] = census["P008007"] / census["P008001"]

# Percent Other Race (responded with "other race" or 2+ races)
census_demos["pct_p_other"] = 1 - (census_demos["pct_p_white"] +
                            census_demos["pct_p_black"] + census_demos["pct_p_native"] + 
                            census_demos["pct_p_asian"] + census_demos["pct_p_pacific"])



# Visually check minimums / maximums for values likely to be "missing" placeholders
  # They seem to be inconsistent in the census data - either NaN or, like, -66666666
for var, _ in acs_demos.iteritems():
    print(var, acs_demos[var].describe())

for var, _ in census_demos.iteritems():
    print(var, census_demos[var].describe())