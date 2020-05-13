from heapq import heapify, heappush, heappop
from pyvisgraph.visible_vertices import edge_distance
import shapefile as shp


def iteritems(d):
    return iter(d.items())


def dijkstra(graph, origin, destination, add_to_visgraph):
    distances = {}  # Distances
    previous = {}  # Previous node in optimal path from source
    queue = PriorityDict()  # Priority queue of all nodes in Graph
    queue[origin] = 0  # Set root node as distance of 0

    for v in queue:
        distances[v] = queue[v]
        if v == destination:
            break
        edges = graph[v]
        if add_to_visgraph is not None and len(add_to_visgraph[v]) > 0:
            edges = add_to_visgraph[v] | graph[v]
        for e in edges:
            w = e.get_adjacent(v)
            elength = distances[v] + edge_distance(v, w)
            if w in distances:
                if elength < distances[w]:
                    raise ValueError
            elif w not in queue or elength < queue[w]:
                queue[w] = elength
                previous[w] = v
    return distances, previous


def shortest_path(graph, origin, destination, add_to_visgraph=None):
    distances, previous = dijkstra(graph, origin, destination, add_to_visgraph)
    path_list = []
    while 1:
        path_list.append(destination)
        if destination == origin:
            break
        destination = previous[destination]
    path_list.reverse()

    # Set up shapefile writer and write path to shapefile
    path_shape = shp.Writer('output/shapefiles/path_shape_l', shp.POINT)
    path_shape.autoBalance = 1  # ensures geometry and attributes match
    path_shape.field("longitude", "F", 10, 8)
    path_shape.field("latitude", "F", 10, 8)
    for point in path_list:
        path_shape.point(point.x, point.y)
        path_shape.record(point.x, point.y)

    path_shape.close()

    return path_list


class PriorityDict(dict):
    """
    Dictionary that can be used as a priority queue.
    Keys of the dictionary are items to be put into the queue, and values
    are their respective priorities. All dictionary methods work as expected.
    The advantage over a standard heapq-based priority queue is that priorities
    of items can be efficiently updated (amortized O(1)) using code as
    'thedict[item] = new_priority.'
    Note that this is a modified version of
    https://gist.github.com/matteodellamico/4451520 where sorted_iter() has
    been replaced with the destructive sorted iterator __iter__ from
    https://gist.github.com/anonymous/4435950
    """
    def __init__(self, *args, **kwargs):
        super(PriorityDict, self).__init__(*args, **kwargs)
        self._rebuild_heap()

    def _rebuild_heap(self):
        self._heap = [(v, k) for k, v in iteritems(self)]
        heapify(self._heap)

    def smallest(self):
        heap = self._heap
        v, k = heap[0]
        while k not in self or self[k] != v:
            heappop(heap)
            v, k = heap[0]
        return k

    def pop_smallest(self):
        heap = self._heap
        v, k = heappop(heap)
        while k not in self or self[k] != v:
            v, k = heappop(heap)
        del self[k]
        return k

    def __setitem__(self, key, val):
        super(PriorityDict, self).__setitem__(key, val)

        if len(self._heap) < 2 * len(self):
            heappush(self._heap, (val, key))
        else:
            self._rebuild_heap()

    def setdefault(self, key, val):
        if key not in self:
            self[key] = val
            return val
        return self[key]

    def update(self, *args, **kwargs):
        super(PriorityDict, self).update(*args, **kwargs)
        self._rebuild_heap()

    def __iter__(self):
        def iterfn():
            while len(self) > 0:
                x = self.smallest()
                yield x
                del self[x]
        return iterfn()