# Load libraries
import pandas as pd
from pandas.io.json import json_normalize 
import numpy as np
import requests
import urllib.request
import json
from datetime import datetime
import datetime as dt
import streamlit as st

#get current date
#datex = datetime.today().strftime('%Y-%m-%d')
datex = '2023-10-01'

#request
res=requests.get(f"https://statsapi.web.nhl.com/api/v1/schedule?startDate=2022-10-01&endDate={datex}").json()
#normalize
data = json_normalize(res,record_path= ['dates','games'])
data = data.drop_duplicates()
#get away team
df1 = data[['gameDate','teams.away.team.name']]
df1 = df1.rename(columns={"teams.away.team.name": "team"})

#get home team
df2 = data[['gameDate','teams.home.team.name']]
df2 = df2.rename(columns={"teams.home.team.name": "team"})

#concat  results
df3 = pd.concat([df1,df2],axis='rows', join='inner')
df3['datex'] = pd.to_datetime(df3['gameDate']).dt.date
df3['datex'] = df3.datex.astype('datetime64[ns]')

df3 = df3.drop('gameDate', axis=1)
df3 = df3.drop_duplicates()
df3 = df3.sort_values(by=['datex'])

#get unique list of teams 
teamlist = df3['team'].tolist()
teamlist = list( dict.fromkeys(teamlist) )
dfmain = pd.DataFrame(columns=['datex','team','roll7','back2back'])

for team in teamlist:
    #isolate to one team
    tmpdf1 = df3.loc[df3['team'] == team]
    #format date
    tmpdf1['datex'] = pd.to_datetime(tmpdf1['datex']).dt.date
    tmpdf1['datex'] = tmpdf1.datex.astype('datetime64[ns]')
    # create all dates dataframe
    tmpdf2 = pd.DataFrame({'datex':pd.date_range(start="2022-10-01",end=datex)})
    #format date
    tmpdf2['datex'] = tmpdf2.datex.astype('datetime64[ns]')
    #merge
    tmpdf3 = tmpdf2.merge(tmpdf1, on='datex', how = 'left')
    #create stats
    tmpdf3['roll7'] = tmpdf3['team'].rolling(7).count()
    tmpdf3['offset'] = tmpdf3.team.shift(1)
    tmpdf3['back2back'] = np.where(tmpdf3.team == tmpdf3.offset, 1, 0)
    #limit columns
    tmpdf3 = tmpdf3[['datex','team','roll7','back2back']]
    #concat
    dfmain = pd.concat([dfmain,tmpdf3], axis='rows')


#create new clean dataframe
dfx = data[['gameDate','teams.away.team.name','teams.home.team.name']]
dfx = dfx.drop_duplicates()

#clean date
dfx['datex'] = pd.to_datetime(dfx['gameDate']).dt.date
dfx['datex'] = dfx.datex.astype('datetime64[ns]')
#rename columns
dfx = dfx.rename(columns={"teams.away.team.name": "away_team","teams.home.team.name": "home_team"})
#drop columns
dfx = dfx.drop('gameDate', axis=1)

#merge away data
dfy = pd.merge(dfx, dfmain, left_on=  ['away_team', 'datex'],
                   right_on= ['team', 'datex'], 
                   how = 'left')

#clean away data
dfy = dfy.rename(columns={"roll7": "away_roll7","back2back": "away_back2back"})
dfy = dfy.drop('team', axis=1)

dfy = pd.merge(dfy, dfmain, left_on=  ['home_team', 'datex'],
                   right_on= ['team', 'datex'], 
                   how = 'left')


#create new clean dataframe
dfx = data[['gamePk','gameDate','teams.away.team.name','teams.home.team.name']]
dfx = dfx.drop_duplicates()

#clean date
dfx['datex'] = pd.to_datetime(dfx['gameDate']).dt.date
dfx['datex'] = dfx.datex.astype('datetime64[ns]')
#rename columns
dfx = dfx.rename(columns={"teams.away.team.name": "away_team","teams.home.team.name": "home_team"})
#drop columns
dfx = dfx.drop('gameDate', axis=1)

#merge away data
dfy = pd.merge(dfx, dfmain, left_on=  ['away_team', 'datex'],
                   right_on= ['team', 'datex'], 
                   how = 'left')
#clean away data
dfy = dfy.rename(columns={"roll7": "away_roll7","back2back": "away_back2back"})
dfy = dfy.drop('team', axis=1)

#merge home data
dfy = pd.merge(dfy, dfmain, left_on=  ['home_team', 'datex'],
                   right_on= ['team', 'datex'], 
                   how = 'left')
#clean home data
dfy = dfy.rename(columns={"roll7": "home_roll7","back2back": "home_back2back"})
dfy = dfy.drop('team', axis=1)

#get other stats
dfz = data[['gamePk','teams.away.score','teams.away.leagueRecord.wins','teams.away.leagueRecord.losses','teams.home.score','teams.home.leagueRecord.wins','teams.home.leagueRecord.losses']]
#merge other stats
dfy = pd.merge(dfy, dfz, left_on=  ['gamePk'],
                   right_on= ['gamePk'], 
                   how = 'left')

dfy = dfy.rename(columns={"teams.away.score": "away_score","teams.home.score": "home_score","teams.away.leagueRecord.wins":"away_wins","teams.home.leagueRecord.wins":"home_wins",
                          "teams.away.leagueRecord.losses":"away_loss","teams.home.leagueRecord.losses":"home_loss",})

def roll7(row):
    if row['away_roll7'] > row['home_roll7']:
        val = 'home'
    elif row['away_roll7'] < row['home_roll7']:
        val = 'away'
    else:
        val = ''
    return val

dfy['roll7_adv'] = dfy.apply(roll7, axis=1)

def back2back(row):
    if row['away_back2back'] > row['home_back2back']:
        val = 'home'
    elif row['away_back2back'] < row['home_back2back']:
        val = 'away'
    else:
        val = ''
    return val

dfy['back2back_adv'] = dfy.apply(back2back, axis=1)

def final(row):
    if row['home_score'] > row['away_score']:
        val = 'home'
    elif row['home_score'] < row['away_score']:
        val = 'away'
    else:
        val = ''
    return val

dfy['final_adv'] = dfy.apply(final, axis=1)

def wins(row):
    if row['home_wins'] > row['away_wins']:
        val = 'home'
    elif row['home_wins'] < row['away_wins']:
        val = 'away'
    else:
        val = ''
    return val

dfy['wins_adv'] = dfy.apply(wins, axis=1)

def loss(row):
    if row['home_loss'] > row['away_loss']:
        val = 'away'
    elif row['home_loss'] < row['away_loss']:
        val = 'home'
    else:
        val = ''
    return val

dfy['loss_adv'] = dfy.apply(loss, axis=1)


dfy['datex'] = pd.to_datetime(dfy['datex']).dt.date

dfy = dfy[[
 'datex',
 'away_team',
 'home_team',
 'roll7_adv',
 'back2back_adv',
 'wins_adv',
 'loss_adv',
 'home_score',
 'home_wins',
 'home_loss',
 'home_roll7',
 'home_back2back',
 'away_score',
 'away_wins',
 'away_loss',
 'away_roll7',
 'away_back2back'
 ]]

xer  = datetime.today().strftime('%Y-%m-%d')
yer  = datetime.today().strftime('%Y-%m-%d')




#start streamlit template
datex = list(dfy['datex'].drop_duplicates())
#teams = list(df['team'].drop_duplicates())
# Sidebar - title & filters
st.sidebar.markdown('### Data Filters')
#teams_choice = st.sidebar.multiselect(
#    "Teams:", teams, default=teams)
#price_choice = st.sidebar.slider(
#    'Max Price:', min_value=4.0, max_value=15.0, step=.5, value=15.0)

start_date, end_date = st.sidebar.date_input('Choose a date range :', [datetime.today(), datetime.today()+dt.timedelta(days=7)])

#greater than the start date and smaller than the end date
mask = (dfy['datex'] > start_date) & (dfy['datex'] <= end_date)

#dfstl = dfy[dfy['datex'].isin(datex_choice)]
dfstl = dfy.loc[mask]
#df = df[df['team'].isin(teams_choice)]
#df = df[df['cost'] < price_choice]

# Main
st.title(f"NHL Systems")

st.markdown('Inspiration https://www.vsin.com/advantage-nhl-rest-vs-tired-matchups/')

rvt = "Rest vs Tired here is expressed as **roll7_adv**. Whichever team is mentioned here has played fewer games on a rolling 7 day basis"
b2b = "We also included a **back2back_adv** metric which indicates which team is playing a back to back game. For instance, if home is the value of back2back_adv, this means the away team played last night and is coming into a back to back contest"

st.markdown(rvt)
st.markdown(b2b)
# Main - dataframes
st.markdown('### Dataframe')

st.dataframe(dfstl.sort_values('datex',
             ascending=False).reset_index(drop=True),1000,1000)