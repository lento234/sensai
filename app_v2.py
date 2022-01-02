import os
import yaml

import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd


# Configurations
config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'config.yml')))

DATA_DIR = os.path.join(os.path.dirname(__file__), config['path'])

# Join device dictionaries
DEFAULT_DEVICES = {}
for device in config['devices']:
    DEFAULT_DEVICES.update(device)
DEFAULT_DEVICES = {f'{value.upper()} ({key})': value.upper() for key, value in DEFAULT_DEVICES.items()}
DEFAULT_DEVICES_KEYS = list(DEFAULT_DEVICES.keys())

DEFAULT_VARS = ['CO2 (ppm)', 'T (°C)', 'RH (%)', 'P (Pa)', 'Ambient Light (ADC)', 'Battery (mV)']

colors = {
    'background': 'white',
    'text': '#2c3e50',
    'theme': 'plotly_white',
}

app = dash.Dash(__name__)

# Load data
def load_data(device_name):
    device_mac = DEFAULT_DEVICES[device_name]
    data_file = os.path.join(DATA_DIR, f"data_{device_mac.replace(':','_')}.csv")
    data = pd.read_csv(data_file, index_col=0, parse_dates=True)
    return data

df = pd.concat([load_data(key) for key in DEFAULT_DEVICES_KEYS],
               keys=[i.split('(')[1].split(')')[0] for i in DEFAULT_DEVICES_KEYS])

df = df.rename_axis(index=['Devices', 'Datetime']).reset_index('Devices').reset_index('Datetime')

fig1 = px.line(df, x='Datetime',
               y=DEFAULT_VARS[0], 
               color='Devices',
               title=DEFAULT_VARS[0],
               template=colors['theme'])
fig1.update_xaxes(
    rangeslider_visible=True,
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1d", step="day", stepmode="backward"),
            dict(count=2, label="2d", step="day", stepmode="backward"),
            dict(count=7, label="1w", step="day", stepmode="backward"),
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(step="all")
        ])
    )
)

fig2 = px.line(df, x='Datetime',
               y=DEFAULT_VARS[1], 
               color='Devices',
               title=DEFAULT_VARS[1],
               template=colors['theme'])

fig3 = px.line(df, x='Datetime',
               y=DEFAULT_VARS[4], 
               color='Devices',
               title=DEFAULT_VARS[4],
               template=colors['theme'])

fig4 = px.scatter(df, x=DEFAULT_VARS[1],
                  y=DEFAULT_VARS[2],
                  color='Devices',
                  marginal_x='box',
                  marginal_y='violin',
                  title=f'{DEFAULT_VARS[1]} vs {DEFAULT_VARS[2]}',
                  template=colors['theme'])

header_text = '''
# SensAI

**Sensor-based Atmospheric Intelligence**
'''

footer_text = '''
Code at [Github](https://github.com/lento234/sensai)

© 2022 Lento Manickathan
'''


app.layout = html.Div(children=[
    html.Div([
        dcc.Markdown(children=header_text)],
             style={
                 'textAlign': 'center',
                 'color': colors['text']
             }
    ),

    dcc.Graph(
        id='fig1',
        figure=fig1
    ),
    dcc.Graph(
        id='fig2',
        figure=fig2
    ),
    dcc.Graph(
        id='fig3',
        figure=fig3
    ),
    dcc.Graph(
        id='fig4',
        figure=fig4
    ),
    html.Div([
        dcc.Markdown(children=footer_text)],
             style={
                 'color': colors['text'],
                 'fontSize': '10px'
             }
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
