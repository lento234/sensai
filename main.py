from functools import lru_cache
import pandas as pd
import yaml
import os

import bokeh
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, PreText, Select


# Configurations
config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'config.yml')))

DATA_DIR = os.path.join(os.path.dirname(__file__), config['path'])
DEFAULT_DEVICES = [device.upper() for device in config['devices']]
DEFAULT_VARS = ['CO2 (ppm)', 'T (°C)', 'RH (%)', 'P (Pa)', 'Ambient Light (ADC)', 'Battery (mV)']

def nix(val, lst):
    return [x for x in lst if x != val]

@lru_cache()
def load_data(device_name):
    data_file = os.path.join(DATA_DIR, f"data_{device_name.replace(':','_')}.csv")
    data = pd.read_csv(data_file, index_col=0, parse_dates=True)
    return data

stats = PreText(text='', width=800)
device = Select(title='Device', options=DEFAULT_DEVICES, value=DEFAULT_DEVICES[0])
var = Select(title='Variable', options=DEFAULT_VARS, value=DEFAULT_VARS[0])

source = ColumnDataSource(data=dict(Datetime=[], variable=[]))
source_static = ColumnDataSource(data=dict(Datetime=[], variable=[]))

tools = 'pan,wheel_zoom,xbox_select,reset'
ts = figure(width=1000, height=500, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts.line(x='Datetime', y='variable', source=source_static)
ts.circle(x='Datetime', y='variable', size=1, source=source, color='None', selection_color="orange")

def device_change(attrname, old, new):
    update()
    
def var_change(attrname, old, new):
    update()
    
def update_stats(data):
    # Get the datetime range
    stats.text = f"{len(data)} datapoints, {data.index[0]} - {data.index[-1]}\n" +\
        data.describe().to_string()

def update():
    device_name = device.value
    variable = var.value
    df = load_data(device_name)
    data = dict(Datetime=df.index.values, variable=df[variable].values)
    source.data = data
    source_static.data = data
    ts.title.text = f"{device_name} - {variable}"
    ts.yaxis.axis_label = variable
    ts.xaxis.axis_label = 'Datetime'
    update_stats(df)

def selection_change(attrname, old, new):
    selected = source.selected.indices
    device_name = device.value
    df = load_data(device_name)
    if selected:
        df = df.iloc[selected,:]
    update_stats(df)

device.on_change('value', device_change)
var.on_change('value', var_change)
source.selected.on_change('indices', selection_change)

# set up layout
dashboard = row(ts, column(device, var))
layout = column(dashboard, stats)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "SensAI"