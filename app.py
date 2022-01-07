import os
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
    "dCO2/dt (ppm/hr)",
    "dT/dt (°C/hr)",
    "P (Pa)",
    "Ambient Light (ADC)",
    "Battery (mV)",
]

colors = {
    "theme": "plotly_white",
}

app = dash.Dash(__name__, title="SensAI")
server = app.server


def calc_ddt(df, var):
    ddt = df[var].ewm(span=config["span"]).mean().diff()
    return ddt


# Load data
def load_data(device_name, dt):
    device_mac = devices[device_name].upper()
    data_file = os.path.join(data_dir, f"data_{device_mac.replace(':','_')}.csv")

    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    if dt:
        df = df[df.index > df.index[-1] - dt]

    df = df.resample(f"{config['resample']}S").mean()

    # Calculate gradients
    df["dCO2/dt (ppm/hr)"] = calc_ddt(df, "CO2 (ppm)") * 3600 / config["resample"]
    df["dT/dt (°C/hr)"] = calc_ddt(df, "T (°C)") * 3600 / config["resample"]

    return df


def get_data(devices, dt):
    df = pd.concat([load_data(key, dt) for key in devices], keys=devices)

    df = (
        df.rename_axis(index=["Devices", "Datetime"])
        .reset_index("Devices")
        .reset_index("Datetime")
    )
    df = df.set_index("Datetime")

    return df


def plot_timedata(df, var):
    key = [i for i in df.columns if var.lower() in i.lower()][0]

    if var in ["dCO2/dt (ppm/hr)", "dT/dt (°C/hr)"]:
        fig = px.area(
            df,
            y=key,
            color="Devices",
            title=key,
            template=colors["theme"],
        )
    else:
        fig = px.line(
            df,
            y=key,
            color="Devices",
            title=key,
            template=colors["theme"],
        )
    fig.update_layout(xaxis=dict(title="Datetime"))

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


def plot_scatter_matrix(df):
    fig = px.scatter_matrix(
        df,
        dimensions=[
            "CO2 (ppm)",
            "T (°C)",
            "RH (%)",
            "dCO2/dt (ppm/hr)",
            "dT/dt (°C/hr)",
            "Ambient Light (ADC)",
        ],
        color="Devices",
        title=f"Scatter matrix",
        template=colors["theme"],
    )
    fig.update_traces(showupperhalf=False, diagonal_visible=False, opacity=0.6, marker=dict(size=4))
    fig.update_layout(height=1000)
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
    fig.update_layout(barmode="overlay")
    fig.update_traces(opacity=0.7)
    return fig


header_text = """
**Sensor-based Atmospheric Intelligence**. Data is collected from [EmpAIR](https://www.empa.ch/web/s405/empair) devices, and processed using
[Dash](https://dash.plot.ly/).
"""

footer_text = """
**© 2021-2022 Lento Manickathan**. Code at [GitHub](https://github.com/lento234/sensai).
"""

app.layout = html.Div(
    [
        html.H1("SensAI"),
        html.Div([dcc.Markdown(id="last-updated", className="last-updated")]),
        html.Div([dcc.Markdown(children=header_text)], className="description"),
        html.Br(),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Datetime", className="label"),
                        dcc.Slider(
                            id="datetime-slider",
                            min=0,
                            max=4,
                            value=1,
                            marks={0: "1d", 1: "2d", 2: "1w", 3: "1m", 4: "all"},
                            className="slider",
                        ),
                    ],
                    className="datetime-slider",
                ),
                html.Div(
                    [
                        html.Label("Var A", className="label"),
                        dcc.Dropdown(
                            id="var-a",
                            options=[{"label": i, "value": i} for i in variables],
                            value="CO2 (ppm)",
                            className="dropdown",
                        ),
                    ],
                    className="var",
                ),
                html.Div(
                    [
                        html.Label("Var B", className="label"),
                        dcc.Dropdown(
                            id="var-b",
                            options=[{"label": i, "value": i} for i in variables],
                            value="T (°C)",
                            className="dropdown",
                        ),
                    ],
                    className="var",
                ),
                html.Br(),
                html.Div(
                    [
                        html.Label("Devices", className="label"),
                        dcc.Dropdown(
                            id="dev",
                            options=[{"label": i, "value": i} for i in devices.keys()],
                            value=list(devices.keys())[:3],
                            multi=True,
                        ),
                    ],
                    className="device-dropdown",
                ),
            ],
            className="controls",
        ),
        html.Br(),
        html.Div(
            [
                dcc.Graph(id="ts-graph-a"),
                html.Br(),
                dcc.Graph(id="ts-graph-b"),
            ],
            className="ts-graphs",
        ),
        html.Br(),
        html.Div(
            [
                html.Div([dcc.Graph(id="stats-graph-a")], className="stats-graphs"),
                html.Div([dcc.Graph(id="stats-graph-b")], className="stats-graphs"),
            ],
            className="stats-graph-container",
        ),
        # html.Div(
        #     [
        #         html.Div(
        #             [dcc.Graph(id="stats-graph-scatter")], className="stats-graphs-scatter"
        #         ),
        #     ],
        #     className="stats-graph-container",
        # ),
        html.Br(),
        html.Div([dcc.Markdown(children=footer_text)], className="description"),
    ],
)


@app.callback(
    Output("ts-graph-a", "figure"),
    Output("ts-graph-b", "figure"),
    Output("stats-graph-a", "figure"),
    Output("stats-graph-b", "figure"),
    Output("last-updated", "children"),
    Input("datetime-slider", "value"),
    Input("var-a", "value"),
    Input("var-b", "value"),
    Input("dev", "value"),
)
def update_figure(dt_value, var_a, var_b, devs):
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

    filtered_df = get_data(devs, dt)

    # Plots
    fig_a = plot_timedata(filtered_df, var_a)
    fig_b = plot_timedata(filtered_df, var_b)
    fig_stats_a = plot_histogram(filtered_df, var_a)
    fig_stats_b = plot_histogram(filtered_df, var_b)

    # Last updated
    last_updated = f'`Last updated: {filtered_df.index.max().strftime("%d %b %Y %H:%M")}`'

    return fig_a, fig_b, fig_stats_a, fig_stats_b, last_updated


if __name__ == "__main__":
    app.run_server(debug=True)
