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


def build_initial_graph(users, users_id, users_info, used_pairs):
    graph = []
    for user1 in users:
        for user2 in users:
            if user1 == user2:
                continue
            if are_close(users_info[user1], users_info[user2]) and (users_id[user1], users_id[user2]) not in used_pairs:
                graph.append([users_id[user1], users_id[user2], calculate_weight(users_info[user1], users_info[user2])])
    return graph


def build_graph_with_history(graph, history, users_id, users_info, users_ind, used_pairs):
    n = len(graph)
    meets = set()
    for previous_match in history:
        for pair in previous_match.to_dict()['match_pairs']:
            meets.add((users_id[pair['user1_id']], users_id[pair['user2_id']]))
            meets.add((users_id[pair['user2_id']], users_id[pair['user1_id']]))
    good_meets = [[] for _ in range(n)]
    for previous_match in history:
        for pair in previous_match.to_dict()['match_pairs']:
            user1 = users_id[pair['user1_id']]
            user2 = users_id[pair['user2_id']]
            if pair['user1_isLike'] == 1 and pair['user2_isLike'] == 1 and (user1, user2) not in meets:
                good_meets[user1].append(user2)
                good_meets[user2].append(user1)
    for i in range(n):
        for user1 in good_meets[i]:
            for user2 in good_meets[i]:
                if calculate_weight(users_info[user1], users_info[user2]) < MATCH_VALUE \
                        and (user1, user2) not in meets and (user1, user2) not in used_pairs:
                    w = (calculate_weight(users_info[user1], users_info[user2]) +
                                       (calculate_weight(users_info[users_ind[i]], users_info[user1]) +
                                        calculate_weight(users_info[users_ind[i]], users_info[user2])) / 2)
                    graph.append([user1, user2, w])
    return graph


def get_users(users_data):
    users = []
    users_info = dict()
    users_id = dict()
    users_ind = []
    cnt = 0
    for user in users_data:
        if user.to_dict()["is_active"]:
            users.append(user.id)
            users_info[user.id] = user.to_dict()
            users_id[user.id] = cnt
            cnt += 1
            users_ind.append(user.id)
    return users, users_info, users_id, users_ind


def get_used_pairs(users_id, history_data):
    used_pairs = set()
    for previous_match in history_data:
        for pair in previous_match.to_dict()['match_pairs']:
            if pair['meeting_happened']:
                user1 = users_id[pair['user1_id']]
                user2 = users_id[pair['user2_id']]
                used_pairs.add((user1, user2))
                used_pairs.add((user2, user1))
    return used_pairs


def build_graph(users_data, history_data):
    users, users_info, users_id, users_ind = get_users(users_data)
    used_pairs = get_used_pairs(users_id, history_data)
    initial_graph = build_initial_graph(users, users_id, users_info, used_pairs)
    graph = build_graph_with_history(initial_graph, history_data, users_id, users_info, users_ind, used_pairs)
    # print(graph)
    return graph, users_ind
