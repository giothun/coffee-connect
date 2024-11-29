from config import MATCH_VALUE, MATCH_COEFFICIENTS, MAX_DISTANCE, NO_EDGE_VALUE


def normalize_string(s):
    return ''.join(e.lower() for e in s if e.isalnum())


def levenshtein_distance(s1, s2):
    dp = [[0 for _ in range(len(s2) + 1)] for _ in range(len(s1) + 1)]

    for i in range(len(s1) + 1):
        dp[i][0] = i
    for j in range(len(s2) + 1):
        dp[0][j] = j

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

    return dp[len(s1)][len(s2)]


def determine_distance(s1, s2):
    s1 = normalize_string(s1)
    s2 = normalize_string(s2)
    return levenshtein_distance(s1, s2)


def calculate_weight(u, v):
    res = 0
    for key in u.keys():
        if key in MATCH_COEFFICIENTS:
            if key == 'interests':
                for interest1 in u[key]:
                    for interest2 in v[key]:
                        if determine_distance(interest1, interest2) <= MAX_DISTANCE[key]:
                            res += MATCH_COEFFICIENTS[key]
            else:
                if determine_distance(u[key], v[key]) <= MAX_DISTANCE[key]:
                    res += MATCH_COEFFICIENTS[key]
    return res


def are_close(u, v):
    return calculate_weight(u, v) >= MATCH_VALUE


def build_initial_graph(data):
    users = []
    users_info = dict()
    users_id = dict()
    users_ind = []
    for i, user in enumerate(data):
        users.append(user.id)
        users_info[user.id] = user.to_dict()
        users_id[user.id] = i
        users_ind.append(user.id)
    graph = [[NO_EDGE_VALUE for _ in range(len(users))] for _ in range(len(users))]
    for user1 in users:
        for user2 in users:
            if user1 == user2:
                continue
            if are_close(users_info[user1], users_info[user2]):
                graph[users_id[user1]][users_id[user2]] = calculate_weight(users_info[user1], users_info[user2])
    return graph, users_ind  # currently kostyl fix later


def build_graph_with_history(users, history):
    # TODO
    initial_graph = build_initial_graph(users)
    return initial_graph


def build_graph(users, history):
    graph = build_graph_with_history(users, history)
    return graph
