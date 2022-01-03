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

data_dir = os.path.join(os.path.dirname(__file__), config["path"])

devices = {}
for device in config["devices"]:
    devices.update(device)

variables = [
    "CO2 (ppm)",
    "T (°C)",
    "RH (%)",
    "P (Pa)",
    "Ambient Light (ADC)",
    "Battery (mV)",
    "dCO2 (dppm)",
]

colors = {
    "text": "#2c3e50",
    "theme": "plotly_white",
}

app = dash.Dash(__name__)
app.title = "SensAI"
server = app.server

# Load data
def load_data(device_name):
    device_mac = devices[device_name].upper()
    data_file = os.path.join(data_dir, f"data_{device_mac.replace(':','_')}.csv")
    data = pd.read_csv(data_file, index_col=0, parse_dates=True)
    return data


def get_data():
    df = pd.concat([load_data(key) for key in devices.keys()], keys=devices.keys())

    df = (
        df.rename_axis(index=["Devices", "Datetime"])
        .reset_index("Devices")
        .reset_index("Datetime")
    )

    df["dCO2 (dppm)"] = df["CO2 (ppm)"].diff()

    return df


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
                            options=[{"label": i, "value": i} for i in variables],
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
                            options=[{"label": i, "value": i} for i in variables],
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
                            options=[{"label": i, "value": i} for i in devices.keys()],
                            value=list(devices.keys())[:3],
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
        dcc.Store(id="filtered-data"),
    ]
)


@app.callback(
    Output("filtered-data", "data"),
    Input("datetime-slider", "value"),
)
def filter_dataset(dt_value):
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

    filtered_df = get_data()

    if dt:
        filtered_df = filtered_df[
            filtered_df.Datetime > filtered_df.Datetime.iloc[-1] - dt
        ]

    return filtered_df.to_json(date_format="iso", orient="split")


# Plot
@app.callback(
    Output("ts-graph-a", "figure"),
    Output("ts-graph-b", "figure"),
    Output("stats-graph-a", "figure"),
    Output("stats-graph-b", "figure"),
    Input("filtered-data", "data"),
    Input("var-a", "value"),
    Input("var-b", "value"),
    Input("dev", "value"),
)
def update_figure(filtered_data, var_a, var_b, devs):
    filtered_df = pd.read_json(filtered_data, orient="split")
    filtered_df = filtered_df[filtered_df["Devices"].isin(devs)]

    fig_a = plot_timedata(filtered_df, var_a)
    fig_b = plot_timedata(filtered_df, var_b)
    fig_stats_a = plot_histogram(filtered_df, var_a)
    fig_stats_b = plot_histogram(filtered_df, var_b)

    return fig_a, fig_b, fig_stats_a, fig_stats_b


if __name__ == "__main__":
    app.run_server(debug=True)
