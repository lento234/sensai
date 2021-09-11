from functools import lru_cache
import pandas as pd
import yaml
import os
#from os.path import dirname, join


from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, PreText, Select
from bokeh.plotting import figure

# Configurations
config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config.yaml')))

DATA_DIR = os.path.join(os.path.dirname(__file__), config['path'])

DEFAULT_DEVICES = config['devices']

def nix(val, lst):
    return [x for x in lst if x != val]

@lru_cache()
def load_data(device):
    fname = os.path.join(DATA_DIR, f"data_{device.replace(':', '_')}.csv")
    data = pd.read_csv(fname, parse_dates=['Datetime'], index_col='Datetime')
    return data

# set up widgets
stats = PreText(text='', width=500)
ticker = Select(value=DEFAULT_DEVICES[0], options=nix(DEFAULT_DEVICES[0], DEFAULT_DEVICES))

# set up plots
source = ColumnDataSource(data=dict(Datetime=[], T=[]))
tools = 'pan,wheel_zoom,xbox_select,reset'

def update(selected=None):
    df = load_data(config['devices'][0])
    update_stats(df)

def update_stats(df):
    stats.text = str(df.describe())

ticker.on_change('value', ticker1_change)

def selection_change(attrname, old, new):
    t1, t2 = ticker1.value, ticker2.value
    data = get_data(t1, t2)
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]
    update_stats(data, t1, t2)

source.selected.on_change('indices', selection_change)

# set up layout
widgets = column(ticker, stats)
series = column(ts1, ts2)
layout = column(main_row, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = "SensAI"
