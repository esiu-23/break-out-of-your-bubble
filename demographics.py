# Demographic Data
# Carolyn Vilter

'''
Contents:
    # Download from API
    # Clean, create vars
    # Clean up dataset
    # Check and export
'''

import pandas as pd
import censusdata


###
# Download via API

# Data extracts using CensusData API package
# Most vars: 2015 ACS 5-year estimates
acs = censusdata.download("acs5", 2015, censusdata.censusgeo([("county", "*")]),
    ["STATE", "COUNTY",    # the basics
    "B05001_001E", "B05001_005E", "B05001_006E",    # citizenship
    "B16002_001E", "B16002_004E", "B16002_007E", "B16002_010E", "B16002_013E",    # limited english
    "B15002_001E", "B15002_003E", "B15002_004E", "B15002_005E", "B15002_006E",
    "B15002_007E", "B15002_008E", "B15002_009E", "B15002_010E", "B15002_011E",
    "B15002_020E", "B15002_021E", "B15002_022E", "B15002_023E", "B15002_024E",
    "B15002_025E", "B15002_026E", "B15002_027E", "B15002_028E",                   # ed attainment
    "B17001_001E", "B17001_002E",    # poverty level
    "B25064_001E",    # median rent
    "B27001_001E", "B27001_005E", "B27001_008E", "B27001_011E", "B27001_014E",
    "B27001_017E", "B27001_020E", "B27001_023E", "B27001_026E", "B27001_029E",
    "B27001_033E", "B27001_036E", "B27001_039E", "B27001_042E", "B27001_045E",
    "B27001_048E", "B27001_051E", "B27001_054E", "B27001_057E"                    # health insurance
    ])

# Race vars: 2010 Decennial Census summary file
census = censusdata.download("sf1", 2010, censusdata.censusgeo([("county", "*")]),
    ["STATE", "COUNTY",    # the basics
    "P008001",    # total pop
    "P008003",    # white alone
    "P008004",    # black or african american alone
    "P008005",    # american indian and alaska native alone
    "P008006",    # asian alone
    "P008007",    # native hawaiian and other pacific islander alone
    "P008008"     # some other race alone
    ])



###
# Clean, create vars

# 1/2: ACS (demos)
acs_demos = pd.DataFrame()
acs_demos["state_fips"] = acs["STATE"]
acs_demos["county_fips"] = acs["COUNTY"]

# Percent of US citizens that are citizens by naturalization
acs_demos["naturalized"] = acs["B05001_005E"] / (acs["B05001_001E"] -
                                                                    acs["B05001_006E"])

# Percent of households with limited English proficiency
acs_demos["limited_english"] = (acs["B16002_004E"] + acs["B16002_007E"] +
                        acs["B16002_010E"] + acs["B16002_013E"]) / acs["B16002_001E"]

# Percent of individuals with highest education attainment HS degree or lower
edvars_men = ["B15002_003E", "B15002_004E", "B15002_005E", "B15002_006E", "B15002_007E",
                "B15002_008E", "B15002_009E", "B15002_010E", "B15002_011E"]
edvars_women = ["B15002_020E", "B15002_021E", "B15002_022E", "B15002_023E", "B15002_024E",
                "B15002_025E", "B15002_026E", "B15002_027E", "B15002_028E"]
acs_demos["low_ed_attain"] = 0
for var in edvars_men + edvars_women:
    acs_demos["low_ed_attain"] += acs[var]
acs_demos["low_ed_attain"] = acs_demos["low_ed_attain"] / acs["B15002_001E"]

# Percent of households below poverty level
acs_demos["below_poverty"] = acs["B17001_002E"] / acs["B17001_001E"]

# Households' median rent
acs_demos["median_rent"] = acs["B25064_001E"]

# Percent with health insurance coverage
insvars_men = ["B27001_005E", "B27001_008E", "B27001_011E", "B27001_014E", "B27001_017E",
                "B27001_020E", "B27001_023E", "B27001_026E", "B27001_029E"]
insvars_women = ["B27001_033E", "B27001_036E", "B27001_039E", "B27001_042E", "B27001_045E",
                "B27001_048E", "B27001_051E", "B27001_054E", "B27001_057E"]
acs_demos["uninsured"] = 0
for var in insvars_men + insvars_women:
    acs_demos["uninsured"] += acs[var]
acs_demos["uninsured"] = acs_demos["uninsured"] / acs["B27001_001E"]


# 2/2: CENSUS (race)
census_demos = pd.DataFrame()
census_demos["state_fips"] = census["STATE"]
census_demos["county_fips"] = census["COUNTY"]

# Percent White
census_demos["white"] = census["P008003"] / census["P008001"]

# Percent Black or African American
census_demos["black"] = census["P008004"] / census["P008001"]

# Percent American Indian and Alaska Native
census_demos["native"] = census["P008005"] / census["P008001"]

# Percent Asian
census_demos["asian"] = census["P008006"] / census["P008001"]

# Percent Native Hawaiian and other Pacific Islander
census_demos["pacific"] = census["P008007"] / census["P008001"]

# Percent Other Race (responded with "other race" or 2+ races)
census_demos["other"] = 1 - (census_demos["white"] +
                            census_demos["black"] + census_demos["native"] +
                            census_demos["asian"] + census_demos["pacific"])



###
# Clean up overall dataset

# Split messy index var into name vars
for df in [acs_demos, census_demos]:
    # Use normal numeric index; make default index into a column
    df.reset_index(inplace=True)
    df["index"] = df["index"].astype(str)

    # Split out county name
    df["county_name"] = df["index"].str.split(",", expand=True)[0]

    # Split out state name
    df["state_draft"] = df["index"].str.split(",", expand=True)[1]
    df["state_name"] = df["state_draft"].str.split(":", expand=True)[0]
    
    acs_demos["state_name"] = acs_demos["state_name"].str.strip()

# Delete process columns
acs_demos.drop(columns = ["index", "state_draft"], inplace=True)
census_demos.drop(columns = ["index", "state_draft"], inplace=True)

# Create single state-county FIPS var - match election data
for df in [acs_demos, census_demos]:
    df["fips"] = df["state_fips"].astype(str).str.zfill(2) + \
                df["county_fips"].astype(str).str.zfill(3)

# Drop Puerto Rico
acs_demos.drop(acs_demos[acs_demos.state_fips == 72].index, inplace=True)
census_demos.drop(census_demos[census_demos.state_fips == 72].index, inplace=True)



###
# Check and save

# Visually check mins / maxes for values likely to be "missing" placeholders
  # They seem to be inconsistent - either NaN or, like, -66666666
for var, _ in acs_demos.iteritems():
    print(var, acs_demos[var].describe())

for var, _ in census_demos.iteritems():
    print(var, census_demos[var].describe())

# Save static version of each data frame
acs_demos.to_csv("data/acs_demos.csv")
census_demos.to_csv("data/census_demos.csv")
