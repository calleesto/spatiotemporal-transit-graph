import pandas as pd
from graph_models import TransitStop, TransitConnection
import time, os, pickle
import sys

sys.setrecursionlimit(50000)

CACHE_FILE = "graph_cache.pkl"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GTFS_FOLDER = os.path.join(BASE_DIR, 'gtfs_data')
stops_path = os.path.join(BASE_DIR, 'gtfs_data', 'stops.txt')
stop_times_path = os.path.join(BASE_DIR, 'gtfs_data', 'stop_times.txt')

def load_nodes(nodes_dict: dict[str, TransitStop]) -> int:
    stops_df = pd.read_csv('./gtfs_data/stops.txt')
    start_time = time.perf_counter() # function timer
    count = 0
    for index, row in stops_df.iterrows():
        stop_id = str(row['stop_id'])

        node = TransitStop(
            node_id=stop_id,
            name=row['stop_name'],
            lat=row['stop_lat'],
            lon=row['stop_lon']
        )

        # filling in the graph_nodes dictionary with node objects
        nodes_dict[stop_id] = node
        count += 1


    end_time = time.perf_counter() # function timer
    execution_time = end_time - start_time

    # function summary
    print(f"loaded {count} nodes")
    print(f"load_nodes took {execution_time:.4f} seconds to finish.")
    return count

def gtfs_time_to_seconds(time_str: str) -> int:
    """converts GTFS time (hh:mm:ss) to total seconds since midnight"""
    h, m, s = map(int, str(time_str).split(':'))
    return h * 3600 + m * 60 + s


def load_edges(nodes_dict: dict[str, TransitStop]) -> int:
    """load edges """
    start_time = time.perf_counter() # function timer
    count = 0

    # format, sort and group csv data
    df = pd.read_csv('./gtfs_data/stop_times.txt') # df = dataframe (virtual spreadsheet)
    df = df.sort_values(by=['trip_id', 'stop_sequence'])
    grouped = df.groupby('trip_id')

    for trip_id, group in grouped:
        stops_in_trip = group.to_dict('records')

        for i in range(len(stops_in_trip) - 1):
            stop_a_data = stops_in_trip[i]
            stop_b_data = stops_in_trip[i + 1]

            node_a_id = str(stop_a_data['stop_id'])
            node_b_id = str(stop_b_data['stop_id'])

            if node_a_id in nodes_dict and node_b_id in nodes_dict:
                dep_time = gtfs_time_to_seconds(stop_a_data['departure_time'])
                arr_time = gtfs_time_to_seconds(stop_b_data['arrival_time'])
                weight = arr_time - dep_time

                trip_info = {
                    'departure': dep_time,
                    'duration': weight,
                    'trip_id': trip_id
                }

                existing = nodes_dict[node_a_id].edges.get(node_b_id)

                if existing is None:
                    edge = TransitConnection(
                        source_node=nodes_dict[node_a_id],
                        target_node=nodes_dict[node_b_id],
                        weight=weight,
                        trip_id=trip_id,
                        route_type="unknown"
                    )
                    edge.schedules.append(trip_info)

                    # add TransitConnection object to the TransitStop's edges dictionary
                    nodes_dict[node_a_id].edges[node_b_id] = edge
                    count += 1
                else:
                    existing.schedules.append(trip_info)

                    if weight < existing.weight:
                        existing.weight = weight

    end_time = time.perf_counter() # function timer
    execution_time = end_time - start_time
    print(f"loaded {count} edges")
    print(f"load_edges took {execution_time:.4f} seconds to finish.")

    return count

def calc_avg_transit_time(nodes_dict: dict[str, TransitStop]):
    for node in nodes_dict.values():
        for edge in node.edges.values():
            if edge.schedules:
                total_duration = sum(trip['duration'] for trip in edge.schedules)
                edge.avg_weight = total_duration / len(edge.schedules)
                edge.avg_weight = total_duration / len(edge.schedules)
            else:
                edge.avg_weight = edge.weight


def build_cache() -> tuple[dict, int, int]:
    graph_nodes = {}
    node_counter = load_nodes(graph_nodes)
    edge_counter = load_edges(graph_nodes)

    calc_avg_transit_time(graph_nodes)

    with open(CACHE_FILE, 'wb') as f:
        pickle.dump((graph_nodes, node_counter, edge_counter), f, protocol=pickle.HIGHEST_PROTOCOL)

    return graph_nodes, node_counter, edge_counter


def read_cache() -> tuple[dict, int, int]:
    with open(CACHE_FILE, 'rb') as f:
        graph_nodes, node_counter, edge_counter = pickle.load(f)

    return graph_nodes, node_counter, edge_counter

def get_or_build_graph(force_build: bool = False) -> tuple[dict, int]:
    # graph_nodes = {} - we use dictionary ({}) instead of a list ([]) to access node objects by their id
    data_downloaded = False
    if not os.path.exists(stops_path) or not os.path.exists(stop_times_path):
        print("GTFS data missing. fetching latest.")
        from data_downloader import fetch_latest_gtfs
        fetch_latest_gtfs()
        data_downloaded = True
    else:
        print("GTFS data found. skipping download.")


    if force_build or data_downloaded or not os.path.exists(CACHE_FILE):
        if force_build:
            print("rebuild flag set to TRUE. forcing cache rebuild")
        elif data_downloaded:
            print("new GTFS data available. rebuilding cache.")
        else:
            print("cache empty. building graph from scratch.")

        graph_nodes, node_counter, edge_counter = build_cache()

    else:
        print("cache contains graph. loading from cache...")
        graph_nodes, node_counter, edge_counter = read_cache()

    print(f"loaded {edge_counter} edges and {node_counter} nodes")
    return graph_nodes, edge_counter

