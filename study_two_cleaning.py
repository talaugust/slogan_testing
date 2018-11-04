

# Import librararies
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
import statsmodels.api as sm
from statistics import mean, stdev

# Set options
pd.set_option('display.max_columns', None)
pd.set_option("display.max_rows",200)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 200)

# Get datasets - make sure dates line up, or some participant ids will not exist in certian places
df_a_b = pd.read_csv('data/footer_results_6_18_18.csv', engine='python')
df_motivations = pd.read_csv('data/all_motivation_6_18_18.csv', engine='python')

df_dem_color = pd.read_csv('data/demographics_color_6_18_18.csv', engine='python')
df_dem_implicit = pd.read_csv('data/demographics_implicit_6_18_18.csv', engine='python')
df_dem_pm = pd.read_csv('data/demographics_PM_6_18_18.csv', engine='python')
df_dem_memory = pd.read_csv('data/demographics_memory_6_18_18.csv', engine='python')
df_dem_thinking_style = pd.read_csv('data/demographics_thinking_style_6_18_18.csv', engine='python')
df_age_color = pd.read_csv('data/color_real_age_6_18_18.csv', engine='python') 


df_slogans = pd.read_csv('data/studythingy.csv', engine='python', sep=';')

### Merge color age results to get age of participants ###
df_dem_color = df_dem_color.merge(df_age_color[['participant_id', 'realAge']], on='participant_id')

### Format Data ###

# rename columns
df_a_b.columns = ['id', 'participant_id', 'data', 'timestamp']
df_motivations.columns = ['index', 'participant_id', 'study', 'data', 'timestamp', 'locale', 'timestamp_1', 'timestamp_2', 'satisficing' ]
df_slogans.columns = ['id', 'slogan', 'contributor_id', 'design_id']
df_dem_pm = df_dem_pm.rename(index=str, columns={"current_time":"timestamp", "country0":"country"})
df_dem_implicit = df_dem_implicit.rename(index=str, columns={"participantId": "participant_id", "current_time":"timestamp", "country0":"country"})
df_dem_color = df_dem_color.rename(index=str, columns={"time_stamp":"timestamp", "current_ctry":"country", "realAge":"age"})
df_dem_memory = df_dem_memory.rename(index=str, columns={"current_time":"timestamp", "country0":"country"})
df_dem_thinking_style = df_dem_thinking_style.rename(index=str, columns={"country0":"country"})


# Add column to slogans for study name
df_slogans = df_slogans.drop(['contributor_id'], axis=1)
df_slogans['study'] = df_slogans.design_id.apply(lambda x: "Implicit Memory" if x > 12 else ("Thinking Style" if x > 6 else "Color"))


# convert json columns to dicts 
df_a_b.data = df_a_b.data.apply(lambda x: json.loads(x))
df_motivations.data = df_motivations.data.apply(lambda x: json.loads(x))

# clean slogan col to just hold slogan string
df_slogans.slogan = df_slogans.slogan.apply(lambda x: json.loads(str.strip(x, '\'')))
df_slogans.slogan = df_slogans.slogan.apply(lambda x: x['slogan'])

# convert timestamps to datetimes
# clear of any timestamps that are 0 first in df_motivations (I think I can ignore this data, but check)
df_motivations = df_motivations[df_motivations['timestamp'] != '0000-00-00 00:00:00']
df_a_b['timestamp'] = pd.to_datetime(df_a_b['timestamp'])
df_motivations['timestamp'] = pd.to_datetime(df_motivations['timestamp'])
df_dem_color['timestamp'] = pd.to_datetime(df_dem_color['timestamp'])
df_dem_implicit['timestamp'] = pd.to_datetime(df_dem_implicit['timestamp'])
df_dem_pm['timestamp'] = pd.to_datetime(df_dem_pm['timestamp'])
df_dem_memory['timestamp'] = pd.to_datetime(df_dem_memory['timestamp'])


# Add study name column for each demographic df
df_dem_color['study_name'] = 'color_age'
df_dem_implicit['study_name'] = 'implicit_memory'
df_dem_memory['study_name'] = 'memory'
df_dem_pm['study_name'] = 'perceptual_models'
df_dem_thinking_style['study_name'] = 'analytic'

# Set indices as participant id #
df_a_b = df_a_b.set_index('participant_id', drop=False)
df_motivations = df_motivations.set_index('participant_id', drop=False)


### Clean + Parse Data ###

# Drop uneccesary columns
df_motivations = df_motivations.drop(['timestamp_1', 'timestamp_2', 'satisficing', 'index'], axis=1)

# Drop rows in motivations and demographics 
# with a timestamp before motivation survey was redeployed (before Febr, 2018)

cut_off_date = dt.datetime(2018, 2, 1) # Original


df_motivations = df_motivations[df_motivations['timestamp'] > cut_off_date]
df_dem_color = df_dem_color[df_dem_color['timestamp'] > cut_off_date]
df_dem_implicit = df_dem_implicit[df_dem_implicit['timestamp'] > cut_off_date]
df_dem_pm = df_dem_pm[df_dem_pm['timestamp'] > cut_off_date]
df_dem_memory = df_dem_memory[df_dem_memory['timestamp'] > cut_off_date]



# Drop any rows in a/b testing without a participant id and all first round of slogan testing (before setups)
df_a_b = df_a_b[df_a_b['participant_id'] != 0]
df_a_b = df_a_b[df_a_b['data'].apply(lambda x: ('slogan' not in x))]

# Get only participants from motivations who finished (i.e. saw a the footer)
df_mot_finished = df_motivations[df_motivations['participant_id'].isin(df_a_b['participant_id'])].copy()

# Seperate the motivation data column into full df, seperate again only the scores (below)
df_motivation_data = df_mot_finished['data'].apply(pd.Series).copy()

# Convert motivations to numeric
df_motivation_data[['bored', 'compare', 'selfLearn', 'science', 'fun']] = df_motivation_data[['bored', 'compare', 'selfLearn', 'science', 'fun']].apply(pd.to_numeric)


print('Number of motivations before taking out people who did not answer at least one:' , len(df_motivation_data))

# Drop any people who put nothing for any motivation (very conservative for now)
df_motivation_data = df_motivation_data.dropna(subset=['bored', 'compare', 'selfLearn', 'science', 'fun'], how='any')
# df_motivation_data_scores = df_motivation_data[['bored', 'compare', 'selfLearn', 'science', 'fun']]

print('Number of motivations after taking out people who did not answer at least one:' , len(df_motivation_data))

# Drop any rows with participant id not with full motivations
df_a_b = df_a_b[df_a_b['participant_id'].isin(df_motivation_data['participant_id'])]

# seperate clickthroughs and setup data
df_clickthrough = df_a_b[df_a_b['data'].apply(lambda x: ((x['data_type'] == 'tracking:a_b_clickthrough')))].copy()
df_setups = df_a_b[df_a_b['data'].apply(lambda x: x['data_type'] == 'tracking:setup')].copy()

# Drop any duplicates in df_clickthrough
df_clickthrough = df_clickthrough.drop_duplicates('participant_id')


# drop any participants without a real age given on the color age test
df_dem_color[df_dem_color['age'] == 0] = np.nan
# df_dem_color = df_dem_color[df_dem_color['age'] > 0]


# In each study, get only the participants who have a corrosponding id in the clickthroughs 
df_dem_color = df_dem_color[df_dem_color['participant_id'].isin(df_motivation_data[df_motivation_data['study_name'] == 'color_age']['participant_id'])]
df_dem_memory = df_dem_memory[df_dem_memory['participant_id'].isin(df_motivation_data[df_motivation_data['study_name'] == 'memory']['participant_id'])]
df_dem_pm = df_dem_pm[df_dem_pm['participant_id'].isin(df_motivation_data[df_motivation_data['study_name'] == 'perceptual_models']['participant_id'])]
df_dem_implicit = df_dem_implicit[df_dem_implicit['participant_id'].isin(df_motivation_data[df_motivation_data['study_name'] == 'implicit_memory']['participant_id'])]
df_dem_thinking_style = df_dem_thinking_style[df_dem_thinking_style['participant_id'].isin(df_motivation_data[df_motivation_data['study_name'] == 'analytic_test']['participant_id'])]


# Convert Perceptual Models df to fit with rest of gender setup 
df_dem_pm.loc[df_dem_pm['gender'] == 1,'gender'] = 4
df_dem_pm.loc[df_dem_pm['gender'] == 2,'gender'] = 5
df_dem_pm.loc[(df_dem_pm['gender'] == 0) | (df_dem_pm['gender'] == 3),'gender'] = 2


df_dem_pm.loc[df_dem_pm['gender'] == 4,'gender'] = 0
df_dem_pm.loc[df_dem_pm['gender'] == 5,'gender'] = 1



# Make a full demographics df
df_dem_full = pd.concat([df_dem_color[['gender', 'age', 'country', 'participant_id', 'study_name']],
            df_dem_implicit[['gender', 'age', 'country', 'participant_id', 'study_name']],
            df_dem_memory[['gender', 'age', 'country', 'participant_id', 'study_name']],
            df_dem_pm[['gender', 'age', 'country', 'participant_id', 'study_name']],
            df_dem_thinking_style[['gender', 'age', 'country', 'participant_id', 'study_name']]])



# Set participant id to numeric and set as index
df_dem_full['participant_id'] = pd.to_numeric(df_dem_full['participant_id'])
df_dem_full = df_dem_full.set_index('participant_id', drop=False)


df_motivation_data['participant_id'] = pd.to_numeric(df_motivation_data['participant_id']) 

### Sync datasets ###
# Just some housekeeping, get all the datasets with correct amounts in them

# Get motivations and demographics in same place
df_mot_dem_data = df_dem_full.merge(df_motivation_data, on='participant_id', how='right')

print('length of other gender :', len(df_mot_dem_data[df_mot_dem_data['gender'] == 2]))
# drop people who put other for gender
df_mot_dem_data = df_mot_dem_data[df_mot_dem_data['gender'] <= 1]


print("length of demographics: ", len(df_dem_full))
print(df_dem_full.dtypes)
print("length of motivations: ", len(df_motivation_data))
print(df_motivation_data.dtypes)
print("length of them together: ", len(df_mot_dem_data))


# convert all participant ids to numeric
df_clickthrough['participant_id'] = pd.to_numeric(df_clickthrough['participant_id'])
df_mot_dem_data['participant_id'] = pd.to_numeric(df_mot_dem_data['participant_id'])

# Drop duplicates 
df_clickthrough= df_clickthrough.drop_duplicates('participant_id')
df_setups = df_setups.drop_duplicates('participant_id')
df_mot_dem_data= df_mot_dem_data.drop_duplicates('participant_id')

# Get only setup rows that relate to a participant who clicked on a slogan
df_clickthrough_setups = df_setups[df_setups['participant_id'].isin(df_clickthrough['participant_id'])].copy()

# Get only set up rows that relate to a participant who did NOT click on a slogan
df_no_clickthrough_setups = df_setups.drop(df_clickthrough.index).copy()


df_clickthrough_data = df_clickthrough.data.apply(pd.Series)
df_setup_data = df_setups.data.apply(pd.Series)
df_no_clickthrough_data = df_no_clickthrough_setups.data.apply(pd.Series)

# rename study_name_x to study_name, drop study_name_x
df_mot_dem_data = df_mot_dem_data.drop('study_name_x', axis=1)
df_mot_dem_data = df_mot_dem_data.rename(index=str, columns={'study_name_y':'study'})

