# Demographic Data
# Carolyn Vilter

'''
Contents:
    # Import election, acs data
    # Join ACS county variable
    # Create/Clean vote variables
'''

import subprocess
import pandas as pd

# Pull election data from box via shell script 
subprocess.run(['bash', 'elections.sh'])

# Read data as pd dfs:
elections = pd.read_csv("data/elections.csv")
acs = pd.read_csv("data/acs_demos.csv")

# Limit elections to 2016; join with cleaner ACS county_name
elections = elections[elections["year"] == 2016]
elections = elections.merge(acs[["fips", "county_name"]], how="left", on="fips")

# Visual scan for correct merge
#elections.head(100)
#elections.tail(100)

# Clean / create vars
elections.drop(columns = ["county"], inplace=True)
elections.rename(columns = {"county_name": "county"}, inplace=True)

elections["dvotes_pct"] = elections["dvotes"]/(elections["dvotes"] + 
                            elections["rvotes"]) * 100
elections["rvotes_pct"] = elections["rvotes"]/(elections["dvotes"] + 
                            elections["rvotes"]) * 100

elections["dvotes_pct"] = elections["dvotes_pct"].round(decimals = 2)
elections["rvotes_pct"] = elections["rvotes_pct"].round(decimals = 2)


# Export cleaned elections
elections.to_csv("data/elections.csv")
