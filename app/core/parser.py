import re

from app.core.type import Graph, Node

RE_RAW_ITEM = re.compile("<(.*?),(.*?)>")


def load(raw: str) -> Graph:
    def get_or_create_node(name: str) -> Node:
        if name not in node_by_name:
            node_by_name[name] = graph.add_node(name)
        return node_by_name[name]

    graph = Graph()
    node_by_name: dict[str, Node] = {}

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        match = RE_RAW_ITEM.search(line)
        if not match:
            raise Exception()

        source_name, target_name = (part.strip() for part in match.groups())
        source = get_or_create_node(source_name)
        target = get_or_create_node(target_name)

        graph.add_edge(source, target)

    return graph
