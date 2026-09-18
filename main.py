from app.core import GraphIO
from app.core import KahnSorter
from app.core import Graph


def main():
    print("Hello from topological!")

    graph = Graph.from_string("""
    <A,B>
    <A,C>
    <B,D>
    <C,D>
    <C,E>
    <D,F>
    <E,F>
    """)

    # graph = Graph.from_string("""
    # <A,A>
    # <B,B>
    # <C,C>
    # """)

    # graph = Graph.from_string("""
    # <A,B>
    # <B,C>
    # <C,A>
    # """)

    raw_paths = KahnSorter(graph).sort()
    for path in [[node.name for node in path] for path in raw_paths]:
        print(" > ".join(path))

    GraphIO.save_graph_to_file("graph.txt", graph)
    GraphIO.save_sorts_to_csv("sort.csv", raw_paths)


if __name__ == "__main__":
    main()
