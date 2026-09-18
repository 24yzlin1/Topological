import copy
from dataclasses import dataclass
import re
from uuid import uuid4

RE_RAW_ITEM = re.compile("<(.*?),(.*?)>")


@dataclass(eq=False)
class Node:
    id: str
    name: str


@dataclass(eq=False)
class Edge:
    id: str
    source: Node
    target: Node


class Graph:
    def __init__(self):
        self.nodes: list[str] = []
        self.node_by_id: dict[str, Node] = {}

        self.edges: list[str] = []
        self.edge_by_id: dict[str, Edge] = {}
        self.edge_keys: set[tuple[str, str]] = set()

        self.adjacency: dict[str, set[str]] = {}
        self.reverse_adjacency: dict[str, set[str]] = {}
        self.in_degree: dict[str, int] = {}

    @classmethod
    def from_string(cls, raw: str) -> "Graph":
        graph = cls()
        node_by_name: dict[str, Node] = {}

        def get_or_create_node(name: str) -> Node:
            if name not in node_by_name:
                node_by_name[name] = graph.add_node(name)
            return node_by_name[name]

        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue

            match = RE_RAW_ITEM.search(line)
            if not match:
                raise ValueError(f"Invalid input format: '{line}'")

            source_name, target_name = (part.strip() for part in match.groups())
            source = get_or_create_node(source_name)
            target = get_or_create_node(target_name)

            graph.add_edge(source, target)

        return graph

    def add_node(self, name: str) -> Node:
        id = str(uuid4())
        node = Node(id, name)

        self.nodes.append(id)
        self.node_by_id[id] = node

        self.adjacency[id] = set()
        self.reverse_adjacency[id] = set()
        self.in_degree[id] = 0

        return node

    def add_edge(self, source: Node, target: Node) -> Edge:
        id = str(uuid4())
        key = (source.id, target.id)

        if source.id == target.id:
            raise ValueError("Self-loop is not allowed")
        if key in self.edge_keys:
            raise ValueError("Duplicate edge")

        edge = Edge(id, source, target)
        self.edges.append(id)
        self.edge_by_id[id] = edge
        self.edge_keys.add(key)

        self.adjacency[source.id].add(target.id)
        self.reverse_adjacency[target.id].add(source.id)
        self.in_degree[target.id] += 1

        return edge

    def remove_edge(self, edge: str) -> bool:
        existing = self.edge_by_id.get(edge)
        if existing is None:
            return False
        else:
            source_id = existing.source.id
            target_id = existing.target.id

            self.edges.remove(edge)
            del self.edge_by_id[edge]
            self.edge_keys.remove((source_id, target_id))

            self.adjacency[source_id].discard(target_id)
            self.reverse_adjacency[target_id].discard(source_id)
            self.in_degree[target_id] -= 1

        for node_id in (source_id, target_id):
            if self.in_degree[node_id] == 0 and not self.adjacency[node_id]:
                self.nodes.remove(node_id)
                del self.node_by_id[node_id]
                del self.adjacency[node_id]
                del self.reverse_adjacency[node_id]
                del self.in_degree[node_id]

            return True

    def get_node(self, id: str) -> Node | None:
        return self.node_by_id.get(id)

    def get_edge(self, id: str) -> Edge | None:
        return self.edge_by_id.get(id)

    def get_adjacency(self) -> dict[str, set[str]]:
        return {
            self.node_by_id[node].name: {
                self.node_by_id[neighbor].name for neighbor in neighbor
            }
            for node, neighbor in self.adjacency.items()
        }

    def get_reverse_adjacency(self) -> dict[str, set[str]]:
        return {
            self.node_by_id[node].name: {
                self.node_by_id[neighbor].name for neighbor in neighbor
            }
            for node, neighbor in self.reverse_adjacency.items()
        }

    def get_in_degree(self) -> dict[str, int]:
        return {
            self.node_by_id[node].name: degree
            for node, degree in self.in_degree.items()
        }

    def is_dag(self):
        in_degree = copy.copy(self.in_degree)
        queue = [node for node in self.nodes if in_degree[node] == 0]
        visited = 0

        while queue:
            node = queue.pop()
            visited += 1
            for neighbor in self.adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited == len(self.nodes)
