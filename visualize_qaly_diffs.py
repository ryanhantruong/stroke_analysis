import data_io
import pandas as pd
import re
from pathlib import Path
import parameters as param
import plotly.graph_objects as go
import plotly.offline as py
import json
import re

#stroke_locations_data_path = Path('/Users/Ryan/Stroke_scripts/stroke_locations/data')
stroke_locations_data_path = Path('/Volumes/dom_dgm_hur$/stroke_data/model_data/stroke_location/data')
fname = Path('NY_MA_NJ_CT_NH_RI_ME_VT_n=10000.csv') # latitude/longitude for all 1000 locations
points = pd.read_csv(stroke_locations_data_path/'points'/fname,index_col='LOC_ID')
chosen_locs = [f'L{i}' for i in range(1000)]
points = points.loc[chosen_locs,:]

map_center = {"lat": points.Latitude.mean(), "lon": points.Longitude.mean()}

MAPBOX_TOKEN = json.loads(open('config/mapbox.json').readline())['token']

addy_path = data_io.DTN_PATH / f'hospital_address_NE_for_stroke_locations.csv'
key_path = data_io.DTN_PATH / f'hospital_keys_master_v2.csv'
addy = pd.read_csv(addy_path, sep='|')
keys = pd.read_csv(key_path, index_col=[1])
addy['HOSP_KEY'] = addy.HOSP_ID.map(keys.HOSP_KEY.to_dict())
addy['MAPBOX_NAME'] = addy.HOSP_KEY + ' ' + addy.OrganizationName
addy['MAPBOX_TYPE'] = addy.CenterType.map({'Comprehensive': 1, 'Primary': 0})
addy = addy.set_index('HOSP_KEY')

# Import percentage of center changes for each location
qalys = pd.read_excel(str(data_io.SUMMARY_ANALYSIS_OUTPUT) + '/qaly_loc_summary.xlsx', 
                index_col=0)
qalys = qalys.iloc[:,0] # just grab qaly diff values
# Merge to get perc of rec changes
points = points.merge(qalys, how='inner', left_index=True, right_index=True)

scatter_list = []

scatter_list.append(
    go.Scattermapbox(lat=points.Latitude,
                 lon=points.Longitude,
                 text=points.index,
                 hoverinfo='text',
                 mode='markers',
                 name='Patient Location',
                 marker=dict(size=9,
                             opacity=0.8,
                             color=points.mean_diff_qaly,
                             colorbar=dict(title="Mean Difference in QALYs Before and After"),
                             colorscale='plasma'))
    )

scatter_list.append(
    go.Scattermapbox(lat=addy.Latitude,
                     lon=addy.Longitude,
                     text=addy.MAPBOX_NAME,
                     hoverinfo='text',
                     mode='markers',
                     name='Center',
                     marker={
                        'color':'gray',
                         'size':
                         13,
                         'symbol':
                         addy.CenterType.map({
                             'Primary': 'pharmacy',
                             'Comprehensive': 'marker'
                         })
                     }))

fig = go.Figure(scatter_list)

#more mapbox styles
# https://plot.ly/python/mapbox-layers/
fig.update_layout(mapbox_style="light",
                  mapbox_accesstoken=MAPBOX_TOKEN,
                  mapbox_zoom=6,
                  mapbox_center=map_center)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.update_layout(legend=go.layout.Legend(x=0,
                                          y=1,
                                          traceorder="normal",
                                          font=dict(size=12, color="black"),
                                          bgcolor="White",
                                          bordercolor="Blue",
                                          borderwidth=2))

fig.write_image(str(data_io.GRAPH_OUTPUT) + '/static/qaly_diff_locations_2_11_21.png')

py.plot(fig, filename=str(data_io.GRAPH_OUTPUT) + '/qaly_diff_locations_2_11_21.html')
