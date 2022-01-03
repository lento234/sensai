import os
from dash.dependencies import Input
from werkzeug.datastructures import auth_property
import yaml

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd


# Configurations
config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "config.yml")))

DATA_DIR = os.path.join(os.path.dirname(__file__), config["path"])

# Join device dictionaries
DEFAULT_DEVICES = {}
for device in config["devices"]:
    DEFAULT_DEVICES.update(device)
DEFAULT_DEVICES = {
    f"{value.upper()} ({key})": value.upper() for key, value in DEFAULT_DEVICES.items()
}
DEFAULT_DEVICES_KEYS = list(DEFAULT_DEVICES.keys())

DEFAULT_VARS = [
    "CO2 (ppm)",
    "T (°C)",
    "RH (%)",
    "P (Pa)",
    "Ambient Light (ADC)",
    "Battery (mV)",
]

colors = {
    "background": "white",
    "text": "#2c3e50",
    "theme": "plotly_white",
}

app = dash.Dash(__name__)
app.title = "SensAI"
server = app.server

# Load data
def load_data(device_name):
    device_mac = DEFAULT_DEVICES[device_name]
    data_file = os.path.join(DATA_DIR, f"data_{device_mac.replace(':','_')}.csv")
    data = pd.read_csv(data_file, index_col=0, parse_dates=True)
    return data


df = pd.concat(
    [load_data(key) for key in DEFAULT_DEVICES_KEYS],
    keys=[i.split("(")[1].split(")")[0] for i in DEFAULT_DEVICES_KEYS],
)

df = (
    df.rename_axis(index=["Devices", "Datetime"])
    .reset_index("Devices")
    .reset_index("Datetime")
)

df["dCO2 (dppm)"] = df["CO2 (ppm)"].diff()
DEFAULT_VARS.append("dCO2 (dppm)")

ranges = {
    "CO2 (ppm)": (350, 1000),
    "dCO2 (dppm)": (-50, 50),
    "T (°C)": (15, 35),
}


def plot_timedata(df, var):
    key = [i for i in df.columns if var.lower() in i.lower()][0]

    fig = px.line(
        df, x="Datetime", y=key, color="Devices", title=key, template=colors["theme"]
    )
    return fig


def plot_scatter(df, var_a, var_b):
    key_a = [i for i in df.columns if var_a.lower() in i.lower()][0]
    key_b = [i for i in df.columns if var_b.lower() in i.lower()][0]
    fig = px.scatter(
        df,
        x=key_a,
        y=key_b,
        color="Devices",
        marginal_x="box",
        marginal_y="violin",
        title=f"{key_a} vs {key_b}",
        template=colors["theme"],
    )
    return fig


def plot_histogram(df, var_a):
    key_a = [i for i in df.columns if var_a.lower() in i.lower()][0]
    fig = px.histogram(
        df,
        x=key_a,
        color="Devices",
        marginal="box",
        title=f"{key_a}",
        template=colors["theme"],
    )
    return fig


header_text = """

**Sensor-based Atmospheric Intelligence**. Data is collected from [EmpAIR](https://www.empa.ch/web/s405/empair) devices, and processed using
[Dash](https://dash.plot.ly/).

"""

footer_text = """
**© 2022 Lento Manickathan**. Code at [GitHub](https://github.com/lento234/sensai).
"""

app.layout = html.Div(
    [
        html.H1("SensAI"),
        html.Div(
            [dcc.Markdown(children=header_text)],
            style={
                "color": colors["text"],
                "display": "block",
                "marginLeft": "auto",
                "marginRight": "auto",
            },
        ),
        html.Br(),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Datetime"),
                        dcc.Slider(
                            id="datetime-slider",
                            min=0,
                            max=4,
                            value=1,
                            marks={0: "1d", 1: "2d", 2: "1w", 3: "1m", 4: "all"},
                        ),
                    ],
                    style={
                        "width": "40%",
                        "color": colors["text"],
                        "textAlign": "center",
                        "float": "left",
                        "display": "inline-block",
                        "padding-right": "5%",
                    },
                ),
                html.Div(
                    [
                        html.Label("Var A"),
                        dcc.Dropdown(
                            id="var-a",
                            options=[{"label": i, "value": i} for i in DEFAULT_VARS],
                            value="CO2 (ppm)",
                        ),
                    ],
                    style={
                        "width": "15%",
                        "color": colors["text"],
                        "textAlign": "center",
                        "display": "inline-block",
                        "padding-right": "1%",
                    },
                ),
                html.Div(
                    [
                        html.Label("Var B"),
                        dcc.Dropdown(
                            id="var-b",
                            options=[{"label": i, "value": i} for i in DEFAULT_VARS],
                            value="T (°C)",
                        ),
                    ],
                    style={
                        "width": "15%",
                        "color": colors["text"],
                        "textAlign": "center",
                        "display": "inline-block",
                    },
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Devices"),
                        dcc.Dropdown(
                            id="dev",
                            options=[
                                {"label": i, "value": i} for i in df.Devices.unique()
                            ],
                            value=df.Devices.unique()[:3],
                            multi=True,
                        ),
                    ],
                    style={
                        "padding-left": "2%",
                        "width": "35%",
                        "color": colors["text"],
                        "textAlign": "center",
                    },
                ),
            ],
            style={
                "width": "95%",
                "display": "block",
                "marginLeft": "auto",
                "marginRight": "auto",
                "color": colors["text"],
            },
        ),
        html.Br(),
        html.Div(
            [
                dcc.Graph(id="ts-graph-a"),
                html.Br(),
                dcc.Graph(id="ts-graph-b"),
            ],
            style={
                "width": "95%",
                "display": "block",
                "marginLeft": "auto",
                "marginRight": "auto",
            },
        ),
        html.Br(),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id="stats-graph-a"),
                    ],
                    style={
                        "width": "40%",
                        "float": "left",
                        "display": "inline-block",
                        "color": colors["text"],
                    },
                ),
                html.Div(
                    [
                        dcc.Graph(id="stats-graph-b"),
                    ],
                    style={
                        "width": "40%",
                        "color": colors["text"],
                        "display": "inline-block",
                    },
                ),
            ],
            style={"display": "flex", "justifyContent": "center"},
        ),
        html.Div(
            [dcc.Markdown(children=footer_text)],
            style={
                "color": colors["text"],
                "display": "block",
                "marginLeft": "auto",
                "marginRight": "auto",
            },
        ),        
    ]
)

# Plot
@app.callback(
    Output("ts-graph-a", "figure"),
    Output("ts-graph-b", "figure"),
    Output("stats-graph-a", "figure"),
    Output("stats-graph-b", "figure"),
    Input("datetime-slider", "value"),
    Input("var-a", "value"),
    Input("var-b", "value"),
    Input("dev", "value"),
)
def update_figure(dt_value, var_a, var_b, dev):
    if dt_value == 0:
        dt = pd.Timedelta(days=1)
    elif dt_value == 1:
        dt = pd.Timedelta(days=2)
    elif dt_value == 2:
        dt = pd.Timedelta(days=7)
    elif dt_value == 3:
        dt = pd.Timedelta(days=30)
    else:
        dt = None
    filtered_df = df[df["Devices"].isin(dev)]
    if dt:
        filtered_df = filtered_df[df.Datetime > df.Datetime.iloc[-1] - dt]

    fig_a = plot_timedata(filtered_df, var_a)
    fig_b = plot_timedata(filtered_df, var_b)
    fig_stats_a = plot_histogram(filtered_df, var_a)
    fig_stats_b = plot_histogram(filtered_df, var_b)

    return fig_a, fig_b, fig_stats_a, fig_stats_b


if __name__ == "__main__":
    app.run_server(debug=True)
