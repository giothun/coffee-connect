
# Number representing the minimal weighted sum needed in order to make an edge between two people
MATCH_VALUE = 3  # I think we can get rid of it

# Default value when there is no edge between 2 vertices
NO_EDGE_VALUE = 1000000

# Constant for the hungarian algorithm
INFINITY = 1000000

# Coefficients with which the parameters are included in the final sum
MATCH_COEFFICIENTS = {
    'year': 1,
    'description': 2,
    'major': 3,
    'interests': 5,
    'degree': 1,
    'country': 3
}

# The maximum allowed levenshtein distance for each parameter
MAX_DISTANCE = {
    'year': 0,
    'description': 10,
    'major': 2,
    'interests': 3,
    'degree': 1,
    'country': 1
}
