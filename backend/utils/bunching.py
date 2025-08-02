def is_bunched(progress_list, threshold_ratio=0.4):
    """
    Given a sorted list of progress values [0, 1), return a set of bunched bus indices.
    """
    if len(progress_list) < 2:
        return set()

    ideal_gap = 1.0 / len(progress_list)
    threshold = threshold_ratio * ideal_gap

    bunched = set()
    n = len(progress_list)

    for i in range(n):
        curr = progress_list[i]
        next_ = progress_list[(i + 1) % n]
        gap = (next_ - curr) % 1.0
        if gap < threshold:
            bunched.add(i)
            bunched.add((i + 1) % n)

    return bunched
