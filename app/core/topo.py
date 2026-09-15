from app.core.type import Graph


class KahnSorter:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.results: list[list[str]] = []

    def sort(self):
        if not self.graph.is_dag():
            raise Exception()
