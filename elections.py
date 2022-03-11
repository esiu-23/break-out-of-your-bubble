# Demographic Data
# Carolyn Vilter

'''
Contents:
    # Import election data
    # Join ACS county variable
    # Create/Clean vote variables
'''

import subprocess

# Import election data from box via shell script 
subprocess.run(['bash', 'elections.sh'])

# 