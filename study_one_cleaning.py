
# Importing librararies
import numpy as np
import csv as csv
import pandas as pd
import math
import json
import datetime as dt
import pprint
from IPython.display import display, HTML
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.sandbox.stats.multicomp import multipletests

# Set options
pd.set_option('display.max_columns', None)
pd.set_option("display.max_rows",200)
pd.set_option('display.max_colwidth', 200)


# Get datasets
df_contributors = pd.read_csv('data/contributor_5_8_18_pre_move.csv', engine='python', sep=';')
df_contributions = pd.read_csv('data//contribution_5_8_18_pre_move.csv', engine='python', sep=';')
df_slogans = pd.read_csv('data/studythingy.csv', engine='python', sep=';')

### Format Data ### 

# Rename columns and drop excess index column for contributors and contributor_id and design_id for slogans
df_contributions.columns = ['id', 'date_created', 'status', 'comparison', 'owner_id']
df_contributors.columns = ['id', 'demographics', 'index2', 'motivations']
df_slogans.columns = ['id', 'slogan', 'contributor_id', 'design_id']

df_contributors = df_contributors.drop(['index2'], axis=1)
df_slogans = df_slogans.drop(['contributor_id'], axis=1)

# Add column to slogans for study name
df_slogans['study'] = df_slogans.design_id.apply(lambda x: "Implicit Memory" if x > 12 else ("Thinking Style" if x > 6 else "Color"))

# Convert demographics and data columns for contributors and contributions, respectively, to dictionaries
df_contributors.demographics = df_contributors.demographics.apply(lambda x: json.loads(str.strip(x, '\'')))
df_contributors.motivations = df_contributors.motivations.apply(lambda x: json.loads(str.strip(x, '\'')))
df_contributions.comparison = df_contributions.comparison.apply(lambda x: json.loads(str.strip(x, '\'')))

# convert timestamps into datetime 
df_contributions['date_created'] = pd.to_datetime(df_contributions['date_created'])

### Clean Data ####

print(len(df_contributors))


# Get cheaters  
df_comments_cheated = df_contributions[df_contributions['comparison'].apply(lambda x: 'comments' in x and x['cheated'] == 'True')]


# Drop particpant 10, who clearly was me who forgot to put taken test as true
df_contributors = df_contributors.drop(10)

# Clean of anyone who did not finish the test
grouped_contributions = df_contributions.groupby('owner_id')
for contr in df_contributors.iterrows():
    choices = len(df_contributions[df_contributions['owner_id'] == contr[1].id])
    try: 
        if (not contr[1].motivations) or (contr[1][1]['taken_test'] == 'True') or (choices > 50) or (contr[1].id in df_comments_cheated['owner_id'].values):
            # Drop from contributors
            df_contributors = df_contributors[df_contributors['id'] != contr[1].id]
            # Drop all contributions from that contributor
            df_contributions = df_contributions[df_contributions['owner_id'] != contr[1].id]
    except KeyError:
        continue

# Drop all contributions from that empty contributor
df_contributors = df_contributors[df_contributors['id'] != 0]
df_contributions = df_contributions[df_contributions['owner_id'] != 0]
     

# Clean of and save comments and new slogans
df_comments = df_contributions[df_contributions['comparison'].apply(lambda x: 'comments' in x)]
df_new_slogans = df_contributions[df_contributions['comparison'].apply(lambda x: 'newSlogan' in x)]
df_contributions = df_contributions[df_contributions['comparison'].apply(lambda x: 'comments' not in x and 'newSlogan' not in x)]

# Break up motivations and demographics into seperate dataframes 
# note they are still contained in df_contributors
# but are now also seperated into full dataframes, rather than a json field
df_motivations = df_contributors['motivations'].apply(pd.Series).copy()
df_demographics = df_contributors['demographics'].apply(pd.Series).copy()

# Add in ids of participants
df_motivations['id'] = df_contributors.id
df_demographics['id'] = df_contributors.id

# Should all be the same
print("Loading, formatting, and cleaning done")
print('Contributors:', len(df_contributors), 'motivations:', len(df_motivations), 'demographics:', len(df_demographics))


# clean slogan col to just hold slogan string
df_slogans.slogan = df_slogans.slogan.apply(lambda x: json.loads(str.strip(x, '\'')))
df_slogans.slogan = df_slogans.slogan.apply(lambda x: x['slogan'])

# df_slogans = df_slogans.set_index('slogan', drop=False)