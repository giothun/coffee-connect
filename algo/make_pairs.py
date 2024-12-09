import database
import graph_builder
import matching


def make_pairs():
    users, history = database.get_data()
    graph, users_ind = graph_builder.build_graph(users, history)
    pairs = matching.create_new_pairs(graph)
    pairs = [(users_ind[i], users_ind[j]) for (i, j) in pairs]
    database.update(pairs)


if __name__ == "__main__":
    make_pairs()
