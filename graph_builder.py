import pandas as pd
from typing import Optional
from graph_models import TransitStop, TransitConnection
from timing import timed
import os, pickle
import sys

sys.setrecursionlimit(50000)

CACHE_FILE = "graph_cache.pkl"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GTFS_FOLDER = os.path.join(BASE_DIR, 'gtfs_data')
STOPS_PATH = os.path.join(GTFS_FOLDER, 'stops.txt')
STOP_TIMES_PATH = os.path.join(GTFS_FOLDER, 'stop_times.txt')


def gtfs_time_converter(time_str: str) -> int:
    """Converts GTFS time (hh:mm:ss) to total seconds. Extended hours (e.g. 25:00) are kept as-is."""
    h, m, s = map(int, str(time_str).split(':'))
    return h * 3600 + m * 60 + s


def gtfs_time_converter_normalized(time_str: str) -> int:
    """Converts GTFS time to seconds on a 0–23h clock (e.g. 25:00 becomes 01:00)."""
    h, m, s = map(int, str(time_str).split(':'))
    h = h % 24
    return h * 3600 + m * 60 + s

def _get_travel_time(stop_a: dict, stop_b: dict) -> int:
    departure = gtfs_time_converter(stop_a['departure_time'])
    arrival = gtfs_time_converter(stop_b['arrival_time'])
    return arrival - departure


def _build_trip_info(stop: dict, trip_id, duration: int) -> dict:
    """returns trips data in a dict"""
    return {
        'departure': gtfs_time_converter_normalized(stop['departure_time']),
        'duration': duration,
        'trip_id': trip_id
    }

def load_nodes(nodes_dict: dict) -> int:
    stops_df = pd.read_csv(STOPS_PATH)

    with timed("load_nodes"):
        for row in stops_df.itertuples():
            stop_id = str(row.stop_id)
            nodes_dict[stop_id] = TransitStop(
                node_id=stop_id,
                name=row.stop_name,
                lat=row.stop_lat,
                lon=row.stop_lon
            )

    count = len(nodes_dict)
    print(f"loaded {count} nodes")
    return count


def load_edges(nodes_dict: dict) -> int:
    count = 0

    read_data = pd.read_csv(STOP_TIMES_PATH)
    sorted_data = read_data.sort_values(by=['trip_id', 'stop_sequence'])
    grouped_data = sorted_data.groupby('trip_id')

    with timed("load_edges"):
        for trip_id, group in grouped_data:
            stop_times_in_trip = group.to_dict('records') # df to dict

            # stop_times_in_trip =     [stop0, stop1, stop2, stop3]
            # stop_times_in_trip[1:] = [stop1, stop2, stop3]
            for current_stop, next_stop in zip(stop_times_in_trip, stop_times_in_trip[1:]):
                node_a_id = str(current_stop['stop_id'])
                node_b_id = str(next_stop['stop_id'])

                # skip if either stop isn't in our graph
                # if node_a_id not in nodes_dict or node_b_id not in nodes_dict:
                #     continue

                duration = _get_travel_time(current_stop, next_stop)
                trip_info = _build_trip_info(current_stop, trip_id, duration)
                existing_edge = nodes_dict[node_a_id].edges.get(node_b_id)

                if existing_edge is None:
                    new_edge = TransitConnection(  # create the edge only ONCE for each pair of stops
                        source_node=nodes_dict[node_a_id],
                        target_node=nodes_dict[node_b_id],
                    )
                    nodes_dict[node_a_id].edges[node_b_id] = new_edge  # store in a's dict - keyed by b's id
                    count += 1

                nodes_dict[node_a_id].edges[node_b_id].trips.append(trip_info)  # record this trip in trips list for this edge

    print(f"loaded {count} edges")
    return count


def annotate_edges_with_avg_duration(nodes_dict: dict) -> None:
    """calculates and stores the average travel time across all trips for each edge"""
    for node in nodes_dict.values():
        for edge in node.edges.values():
            if edge.trips:
                total_duration = sum(trip['duration'] for trip in edge.trips)
                edge.avg_duration = total_duration / len(edge.trips)
            else:
                edge.avg_duration = None


def build_cache() -> tuple:
    graph_nodes = {}
    node_counter = load_nodes(graph_nodes)
    edge_counter = load_edges(graph_nodes)
    annotate_edges_with_avg_duration(graph_nodes)

    with open(CACHE_FILE, 'wb') as f:
        pickle.dump((graph_nodes, node_counter, edge_counter), f, protocol=pickle.HIGHEST_PROTOCOL)

    return graph_nodes, node_counter, edge_counter


def read_cache() -> tuple:
    with open(CACHE_FILE, 'rb') as f:
        graph_nodes, node_counter, edge_counter = pickle.load(f)
    return graph_nodes, node_counter, edge_counter


def _rebuild_reason(force_build: bool, data_downloaded: bool) -> Optional[str]:
    if force_build:
        return "rebuild flag set to TRUE"
    if data_downloaded:
        return "new GTFS data downloaded"
    if not os.path.exists(CACHE_FILE):
        return "no cache found"
    return None


def get_or_build_graph(force_build: bool = False) -> tuple:
    data_downloaded = False

    if not os.path.exists(STOPS_PATH) or not os.path.exists(STOP_TIMES_PATH):
        print("GTFS data missing — fetching latest.")
        from data_downloader import fetch_latest_gtfs
        fetch_latest_gtfs()
        data_downloaded = True
    else:
        print("GTFS data found — skipping download.")

    reason = _rebuild_reason(force_build, data_downloaded)

    if reason:
        print(f"{reason} — building graph from scratch.")
        graph_nodes, node_counter, edge_counter = build_cache()
    else:
        print("loading graph from cache...")
        graph_nodes, node_counter, edge_counter = read_cache()

    print(f"loaded {edge_counter} edges and {node_counter} nodes")
    return graph_nodes, edge_counter