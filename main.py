import os
from dash import Dash, dcc, html, Input, Output
from graph_builder import get_or_build_graph
from visualizer import draw_graph

FORCE_REBUILD = False
nodes, total_edges = get_or_build_graph(force_build=FORCE_REBUILD)


def format_time(hour_float):
    hours = int(hour_float)
    minutes = int((hour_float - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"

current_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(current_dir, 'assets')

app = Dash(__name__, assets_folder=assets_dir)

app.layout = html.Div(
    style={'backgroundColor': '#050505', 'height': '100vh', 'margin': '0', 'display': 'flex',
           'flexDirection': 'column'},
    children=[
        html.Div(
            style={
                'padding': '10px 20px', 'backgroundColor': '#0a0a0a', 'display': 'flex',
                'alignItems': 'center', 'justifyContent': 'center', 'borderBottom': '1px solid #1a1a1a', 'gap': '30px'
            },
            children=[
                html.Div(
                    style={'width': '33vw'},
                    children=[
                        dcc.Slider(
                            id='time-slider', min=0, max=23.75, step=0.25, value=15, marks=None, updatemode='drag'
                        )
                    ]
                ),
                html.Div(
                    id='time-display',
                    style={
                        'color': '#00ffcc', 'fontFamily': 'monospace', 'fontSize': '24px',
                        'fontWeight': 'bold', 'textShadow': '0 0 10px #00ffcc', 'minWidth': '100px'
                    }
                ),
            ]
        ),
        html.Div(
            style={
                'display': 'flex', 'justifyContent': 'center', 'gap': '30px',
                'padding': '8px', 'backgroundColor': '#070707', 'borderBottom': '1px solid #111',
                'color': '#888', 'fontFamily': 'monospace', 'fontSize': '13px'
            },
            children=[
                html.Span([html.Span("■", style={'color': '#00ff44', 'textShadow': '0 0 8px #00ff44'}), " Faster than scheduled"]),
                html.Span([html.Span("■", style={'color': '#00aaff', 'textShadow': '0 0 8px #00aaff'}), " On schedule"]),
                html.Span([html.Span("■", style={'color': '#ff0033', 'textShadow': '0 0 8px #ff0033'}), " Heavy delays"]),
                html.Span([html.Span("■", style={'color': '#333333'}), " No service"]),
            ]
        ),
        html.Div(
            style={'flex': '1'},
            children=[
                dcc.Graph(
                    id='transit-graph',
                    figure=draw_graph(graph_nodes=nodes, selected_time_sec=15 * 3600),
                    style={'height': '100%', 'width': '100vw'},
                    config={'displayModeBar': False}
                )
            ]
        )
    ]
)

@app.callback(
    [Output('time-display', 'children'),
     Output('transit-graph', 'figure')],
    [Input('time-slider', 'value')]
)
def update_dashboard(value):
    time_label = format_time(value)

    selected_time_sec = int(value * 3600)
    new_fig = draw_graph(graph_nodes=nodes, selected_time_sec=selected_time_sec)

    return time_label, new_fig


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)