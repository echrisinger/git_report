from typing import List


def get_matching_entry(entries: List[str], path):
    def wildcard_postfix(s): return r"{}*".format(s)
    return next(iter([
        e
        for e in entries
        if re.search(wildcard_postfix(e), path)
    ]), None)
