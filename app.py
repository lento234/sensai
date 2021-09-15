from functools import lru_cache
import pandas as pd
import numpy as np
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

@lru_cache()
def load_data(device_name):
    data_file = os.path.join(DATA_DIR, f"data_{device_name.replace(':','_')}.csv")
    data = pd.read_csv(data_file, index_col=0, parse_dates=True)
    return data

stats = PreText(text='', width=800)
device = Select(title='Device', options=DEFAULT_DEVICES, value=DEFAULT_DEVICES[0])
var1 = Select(title='Variable 1', options=DEFAULT_VARS, value=DEFAULT_VARS[0])
var2 = Select(title='Variable 2', options=DEFAULT_VARS, value=DEFAULT_VARS[1])

source = ColumnDataSource(data=dict(Time=[], t1=[], t2=[]))
source_static = ColumnDataSource(data=dict(Time=[], t1=[], t2=[]))

tools = 'pan,wheel_zoom,xbox_select,reset,crosshair'
#tools="crosshair,pan,reset,save,wheel_zoom",


ts1 = figure(width=1000, height=250, tools=tools,
             x_axis_type='datetime', active_drag="xbox_select")
ts1.axis.axis_label_text_font_style = "bold"


ts1.line(x='Time', y='t1', source=source_static, line_width=2)
ts1.circle(x='Time', y='t1', size=3, source=source, color='None', selection_color="orange")

ts2 = figure(width=1000, height=250, tools=tools,
             x_axis_type='datetime', active_drag="xbox_select")
ts2.xaxis.axis_label = 'Time'
ts2.axis.axis_label_text_font_style = "bold"

ts2.line(x='Time', y='t2', source=source_static, line_width=2)
ts2.circle(x='Time', y='t2', size=2, source=source, color='None', selection_color="orange")

corr = figure(width=500, height=500,
              tools=tools)
corr.axis.axis_label_text_font_style = "bold"
corr.circle('t1', 't2', size=3, source=source,
            selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)


def update_stats(data):
    # Get the datetime range
    stats.text = f"{len(data)} datapoints, {data.index[0]} - {data.index[-1]}\n" +\
        data.describe().to_string()

def update():
    device_name = device.value
    variable1 = var1.value
    variable2 = var2.value
    df = load_data(device_name)
    data = dict(Time=df.index, t1=df[variable1], t2=df[variable2])
    source.data = data
    source_static.data = data
    ts1.yaxis.axis_label = variable1
    ts2.yaxis.axis_label = variable2
    corr.title.text = f'{variable1} vs. {variable2}'
    corr.xaxis.axis_label = variable1
    corr.yaxis.axis_label = variable2
    
    update_stats(df)

def selection_change(attrname, old, new):
    selected = source.selected.indices
    device_name = device.value
    df = load_data(device_name)
    if selected:
        df = df.iloc[selected,:]
    update_stats(df)

device.on_change('value', lambda attr, old, new: update())
var1.on_change('value', lambda attr, old, new: update())
var2.on_change('value', lambda attr, old, new: update())
source.selected.on_change('indices', selection_change)

# set up layout
summary = row(column(device, var1, var2), stats)
dashboard = row(column(ts1, ts2), corr)
layout = column(summary, dashboard)

# initialize
update()

curdoc().title = "SensAI"
curdoc().add_root(summary)
curdoc().add_root(dashboard)
