class TransitStop:
    def __init__(self, node_id, name, lat, lon):
        self.id = node_id
        self.edges = {}
        self.name = name
        self.lat = lat
        self.lon = lon

class TransitConnection:
    def __init__(self, source_node, target_node):
        self.source = source_node
        self.target = target_node
        self.trips = []
        self.avg_duration = None  # calculated after all trips are loaded