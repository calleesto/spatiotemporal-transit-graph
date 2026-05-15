class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.edges = {}

class Edge:
    def __init__(self, source_node, target_node, weight):
        self.source = source_node
        self.target = target_node
        self.weight = weight

class TransitStop(Node):
    def __init__(self, node_id, name, lat, lon):
        super().__init__(node_id)
        self.name = name
        self.lat = lat
        self.lon = lon

class TransitConnection(Edge):
    def __init__(self, source_node, target_node, weight, trip_id, route_type):
        super().__init__(source_node, target_node, weight)
        self.trip_id = trip_id
        self.route_type = route_type
        self.schedules = []
        self.avg_weight = 0