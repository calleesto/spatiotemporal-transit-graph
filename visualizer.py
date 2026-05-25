from typing import Optional
import plotly.graph_objects as go
from graph_models import TransitStop
from timing import timed

THRESHOLD = 0.05
TIME_WINDOW = 1800  # 30 min


def _get_mean_duration_in_window(edge, selected_time_sec: int, time_window: int) -> Optional[float]:
    if selected_time_sec is None:
        return None

    trips_in_window = [t for t in edge.trips if abs(t['departure'] - selected_time_sec) <= time_window]
    if not trips_in_window:
        return None

    return sum(t['duration'] for t in trips_in_window) / len(trips_in_window)


def _extract_nodes(graph_nodes: dict):
    x, y, text = [], [], []
    for node in graph_nodes.values():
        x.append(node.lon)
        y.append(node.lat)
        text.append(node.name)
    return x, y, text


def _lib_draw(grey_x, grey_y, green_x, green_y, blue_x, blue_y, red_x, red_y, hover_x, hover_y, hover_text, node_x,
              node_y, node_text):
    fig = go.Figure()

    # no service edge color
    fig.add_trace(go.Scatter(x=grey_x, y=grey_y, line=dict(width=0.5, color='#333333'), mode='lines', hoverinfo='none'))

    # faster than average edge color
    fig.add_trace(
        go.Scatter(x=green_x, y=green_y, line=dict(width=2.0, color='#00ff44'), mode='lines', hoverinfo='none'))

    # on schedule edge color
    fig.add_trace(go.Scatter(x=blue_x, y=blue_y, line=dict(width=0.5, color='#00aaff'), mode='lines', hoverinfo='none'))

    # heavy delays edge color
    fig.add_trace(go.Scatter(x=red_x, y=red_y, line=dict(width=2.5, color='#ff0033'), mode='lines', hoverinfo='none'))

    # invisible markers at edge midpoints for hover detection
    fig.add_trace(go.Scatter(
        x=hover_x, y=hover_y, mode='markers', hoverinfo='text', text=hover_text,
        marker=dict(size=7, color='rgba(0,0,0,0)'),
        hoverlabel=dict(bgcolor='#111111', font=dict(color='#00ffcc'), bordercolor='#333333')
    ))

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode='markers', hoverinfo='text', text=node_text,
        marker=dict(color='#00ffcc', size=3, line_width=0)
    ))

    fig.update_layout(
        showlegend=False, hovermode='closest', margin=dict(b=0, l=0, r=0, t=0),
        plot_bgcolor='#050505', paper_bgcolor='#050505',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    return fig


def draw_graph(graph_nodes: dict, selected_time_sec: int = None):
    with timed("draw_graph"):
        return _draw_graph(graph_nodes, selected_time_sec)


def _draw_graph(graph_nodes: dict, selected_time_sec: int = None):
    green_x, green_y = [], []
    red_x, red_y = [], []
    blue_x, blue_y = [], []
    grey_x, grey_y = [], []

    hover_x, hover_y, hover_text = [], [], []

    # tracking drawn edges to avoid duplicates
    drawn_edges = set()

    for node in graph_nodes.values():
        for edge in node.edges.values():
            a, b = edge.source, edge.target
            edge_id = f"{a.id}-{b.id}"

            if edge_id in drawn_edges:
                continue
            drawn_edges.add(edge_id)

            # none creates segments to tell plotly to lift the pen
            coords_x = [a.lon, b.lon, None]
            coords_y = [a.lat, b.lat, None]
            # midpoint for hover marker
            mid_x, mid_y = (a.lon + b.lon) / 2, (a.lat + b.lat) / 2

            avg_duration = edge.avg_duration
            base_popup = f"<b>{a.name} ➔ {b.name}</b><br>Avg duration: {avg_duration:.0f}s"

            current_duration = _get_mean_duration_in_window(edge, selected_time_sec, TIME_WINDOW)

            if current_duration is None:
                grey_x.extend(coords_x)
                grey_y.extend(coords_y)

                hover_x.append(mid_x)
                hover_y.append(mid_y)
                status = "No active trips" if selected_time_sec else "N/A"
                hover_text.append(f"{base_popup}<br>Current duration: {status}")
            else:
                if current_duration < avg_duration * (1 - THRESHOLD):
                    green_x.extend(coords_x)
                    green_y.extend(coords_y)
                elif current_duration > avg_duration * (1 + THRESHOLD):
                    red_x.extend(coords_x)
                    red_y.extend(coords_y)
                else:
                    blue_x.extend(coords_x)
                    blue_y.extend(coords_y)

                hover_x.append(mid_x)
                hover_y.append(mid_y)
                hover_text.append(f"{base_popup}<br>Current duration: {current_duration:.0f}s")

    node_x, node_y, node_text = _extract_nodes(graph_nodes)

    return _lib_draw(
        grey_x, grey_y, green_x, green_y, blue_x, blue_y, red_x, red_y,
        hover_x, hover_y, hover_text, node_x, node_y, node_text
    )