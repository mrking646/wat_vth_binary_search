def find_key_path(nested_dict, target_value):
    """
    Finds the path to the given target_value in a nested dictionary.

    :param nested_dict: The nested dictionary to search.
    :param target_value: The value to find.
    :return: A list of tuples, where each tuple contains the path to an occurrence of the target_value.
    """
    def search(sub_dict, path):
        if isinstance(sub_dict, dict):
            for key, value in sub_dict.items():
                if value == target_value:
                    paths.append((*path, key))
                elif isinstance(value, dict):
                    search(value, path + (key,))

    paths = []
    search(nested_dict, ())
    return paths

# Example usage
temp_dict = {
    'HCI_Wg_10_Lg_0p13': {
        'site0': {'drain': 'SMU1/0', 'source': 'SMU1/1', 'bulk': 'SMU1/2', 'gate': 'SMU1/3'},
        'site1': {'drain': 'SMU1/4', 'source': 'SMU1/5', 'bulk': 'SMU1/6', 'gate': 'SMU1/7'}
    },
    'HCI_Wg_10_Lg_0p3': {
        'site0': {'drain': 'SMU1/8', 'source': 'SMU1/9', 'bulk': 'SMU1/10', 'gate': 'SMU1/11'},
        'site1': {'drain': 'SMU1/12', 'source': 'SMU1/13', 'bulk': 'SMU1/14', 'gate': 'SMU1/15'}
    }
}

target_value = 'SMU1/2'
result = find_key_path(temp_dict, target_value)
print(result)
