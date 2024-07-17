def find_range(current):
    current_ranges = [10e-9, 100e-9, 1e-6, 10e-6, 100e-6, 1e-3, 10e-3]
    # Find the closest range to the given current, the range should be bigger than the current
    for i in range(len(current_ranges)):
        if current_ranges[i] > current:
            return current_ranges[i]
    


def test_find_range():
    assert find_range(5e-6) == 10e-6
    assert find_range(6e-9) == 10e-9
    assert find_range(4e-3) == 10e-3

# test_find_range()