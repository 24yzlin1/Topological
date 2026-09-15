from app.core.parser import load_graph_from_string
from app.core.topo import KahnSorter


def main():
    print("Hello from topological!")

    graph = load_graph_from_string("""
    <A,B>
    <A,C>
    <B,D>
    <C,D>
    <C,E>
    <D,F>
    <E,F>
    """)

    # graph = load_graph_from_string("""
    # <A,A>
    # <B,B>
    # <C,C>
    # """)

    # graph = load_graph_from_string("""
    # <A,B>
    # <B,C>
    # <C,A>
    # """)

    raw_paths = KahnSorter(graph).sort()
    for path in [[node.name for node in path] for path in raw_paths]:
        print(" > ".join(path))


if __name__ == "__main__":
    main()
