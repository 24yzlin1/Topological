import copy
import time

from app.core.type import Graph, Node


class KahnSorter:
    def __init__(self, graph: Graph):
        self.graph = graph

    def _sort(self):
        if not self.graph.is_dag():
            raise ValueError("Graph contains a cycle; topological sort is not possible")

        nodes = copy.copy(self.graph.nodes)
        adjacency = copy.copy(self.graph.adjacency)
        in_degree = copy.copy(self.graph.in_degree)

        used: dict[str, bool] = {node: False for node in nodes}
        path: list[str] = []
        output: list[list[str]] = []

        def _dfs():
            if len(nodes) == len(path):
                output.append(copy.copy(path))
                return

            for node in nodes:
                if used[node] or in_degree[node] != 0:
                    continue

                used[node] = True
                path.append(node)
                for neighbor in adjacency[node]:
                    in_degree[neighbor] -= 1

                _dfs()

                for neighbor in adjacency[node]:
                    in_degree[neighbor] += 1
                path.pop()
                used[node] = False

        _dfs()

        return output

    def sort(self) -> list[list[Node]]:
        return [[self.graph.get_node(node) for node in path] for path in self._sort()]  # type: ignore

    def sort_with_benchmark(self) -> tuple[list[list[Node]], float]:
        start = time.perf_counter()
        result = self.sort()
        end = time.perf_counter()

        return result, end - start
