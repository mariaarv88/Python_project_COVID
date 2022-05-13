import numpy as np
import pandas as pd
from scipy import signal

df=pd.read_csv("https://raw.githubusercontent.com/Sandbird/covid19-Greece/master/cases.csv",parse_dates=["date"])
df=df.set_index("date")
df=df.drop(["id"],axis=1)
df["new_positive_tests"]=df.positive_tests.diff()
df["new_vaccinations"]=df['total_vaccinations'].diff()
from scipy.stats import gamma
k=2209/290
t=(29/47)
dist=gamma(k,scale=t)

def Rt(df,ix0=-1,smooth="10D",k=2209/290,t=29/47):
    Irm=df.rolling(smooth).mean().new_cases
    s=0
    dist=gamma(k,scale=t)
    for ix in range(0,15):    
        s+=dist.pdf(ix)*Irm[ix0-ix]
        #print(ix,ix0-ix,Irm[ix0-ix],Irm[ix0]/s) 
    return Irm[ix0]/s

df["Rt"]=np.nan
for i in range(len(df)):
    df["Rt"].iloc[i]=Rt(df,i)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


st.set_page_config(layout="wide")
st.title('Greece covid analytics Dashboard')


# Index(['new_cases', 'confirmed', 'new_deaths', 'total_deaths', 'new_tests',
#        'positive_tests', 'new_selftest', 'total_selftest', 'new_ag_tests',
#        'ag_tests', 'total_tests', 'new_critical', 'total_vaccinated_crit',
#        'total_unvaccinated_crit', 'total_critical', 'hospitalized',
#        'discharged', 'icu_out', 'icu_percent', 'beds_percent', 'new_active',
#        'active', 'recovered', 'total_foreign', 'total_domestic',
#        'total_unknown', 'total_vaccinations', 'reinfections'],
#       dtype='object')

value_labels={"New Cases":'new_cases',"Rt":"Rt","New Tests":'new_tests',"New Positive Tests":"new_positive_tests",
              "New Deaths":'new_deaths',"New Hospitalizations":"hospitalized","New Critical":"new_critical","ICU out":"icu_out",
             "New Vaccinations":"new_vaccinations","Total Vaccinations":"total_vaccinations"}


Rows={"Cases and Testing":["New Cases","Rt","New Tests","New Positive Tests"],
     "Hospitalization and Mortallity":["New Hospitalizations","New Critical","New Deaths","ICU out"],
      "Vaccinations":["Total Vaccinations",'','','']
     }


for Row in Rows: #Row is every key in dictionary Rows 
    # loop 0: Row="Cases and Testing" , Rows[Row]=["New Cases","Rt","New Tests","New Positive Tests"]
    cols = st.columns(tuple([0.5]+[1]*len(Rows[Row]))) #tuple([0.5]+[1]*len(Rows[Row]))= (0.5,1,1,1,1)

    with cols[0]:
        st.markdown(Row)

    #zip 
    #for i,j,k in zip(['a','b','c'],[1,2,3],[7,8,9]):
    #i='a',j=1,k=7
    #'b',2,8
    #'c',3,9

    for ci,label in zip(cols[1:],Rows[Row]):
        #loop 0: ci = cols[1], label="New Cases"
        if label != '':
            info=value_labels[label] #name of the corresponding column in dataframe
            if np.isfinite(df.iloc[-1][info]) and np.isfinite(df.iloc[-2][info]):
                val=df.iloc[-1][info]
                dif=df.iloc[-1][info]-df.iloc[-2][info]
            else: 

                #it is only about Hospitalizations, which is around one day before
                notna=df[~pd.isna(df[info])] #temporary dataframe (with random name notna), without nan values
                #pd.isna(df[info]) is True where the dataframe is NaN
                #~pd.isna(df[info]) is True where the dataframe is NOT NaN

                val=notna.iloc[-1][info] #last not NaN value (not latest day!)
                dif=notna.iloc[-1][info]-notna.iloc[-2][info] # last not NaN value - second last not NaN value

            if label != "Rt":
                # Show the values as integers
                ci.metric(label=label,value= int(val), delta = str(int(dif)), delta_color = 'inverse')
            elif label == "New Tests":
                # If is lower make it red!
                ci.metric(label=label,value= round(val,2), delta = str(round(dif,2)), delta_color = 'normal')
            else:
                ci.metric(label=label,value= round(val,2), delta = str(round(dif,2)), delta_color = 'inverse')



row_spacer_start, row1, row2, row_spacer_end  = st.columns((0.1, 1.0, 6.4, 0.1))

with row1:
    #add here everything you want in first column
    plot_value = st.selectbox ("Variable", list(value_labels.keys()), key = 'value_key') #take all the keys from value_labels dictionary
    plot_value2 = st.selectbox ("Second Variable", [None]+list(value_labels.keys()), key = 'value_key')
    smooth = st.checkbox("Add smooth curve")


with row2:    
    sec= not (plot_value2 is None) #True or False if there is a second plot

    fig = make_subplots(specs=[[{"secondary_y": sec}]]) #plotly function, define fig which will be show at iser

    x1=df.index #abbreviation for dates
    y1=df[value_labels[plot_value]] #abbreviation for ploting values, translate from shown names to column names (from value_labels dictionary)

    #fig1= px.bar(df,x = x1, y=value_labels[plot_value])#,log_y=log)

    fig1= px.bar(df,x = x1, y=y1) #bar plot named as fig1

    fig.add_traces(fig1.data) #add to the fig (what is going to be show to the user) the fig1


    fig.layout.yaxis.title=plot_value #add label

    if smooth:
        # Create temprary rolling average dataframe
        ys1= df.rolling("7D").mean()[value_labels[plot_value]]
        figs=px.line(x = x1, y=ys1)#,log_y=log)
        fig.add_traces(figs.data)   #add figs to the fig (what we will show at the end)     

    if sec:
        x2=df.index
        y2=df[value_labels[plot_value2]]
        figsec=px.line(x = x2, y=y2)#,log_y=log)
        figsec.update_traces(yaxis="y2")

        fig.add_traces(figsec.data) #add figsec to the fig (what we will show at the end) 
        fig.layout.yaxis2.title=plot_value2

    fig.update_layout(title_x=0,margin= dict(l=0,r=10,b=10,t=30), yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True) 
