import os
import subprocess
from typing import List

import git
from git_report.strings import get_matching_entry


def is_git_repo(path) -> bool:
    try:
        _ = git.Repo(path)
        return True
    except git.exc.InvalidGitRepositoryError:
        return False


def find_all_root_repos(root_path) -> List[str]:
    abs_root_path = os.path.abspath(root_path)
    stack = []
    stack.append(abs_root_path)

    root_directories = set()

    while len(stack):
        path = stack.pop()

        if is_git_repo(path):
            root_directories.add(path)
        else:
            directories = [
                _get_abs_path(path, entry)
                for entry in os.listdir(path)
                if os.path.isdir(_get_abs_path(path, entry))
            ]
            for d in directories:
                stack.append(d)

    return root_directories


def is_file_ignored(file_path):
    """
    example git command output:

    M README.md
    ?? bin/observer.py
    !! .vscode/
    !! git_report.egg-info/
    !! git_report/__pycache__/
    !! venv/
    """
    repo = git.Repo(file_path, search_parent_directories=True)
    status_files_with_ignored = repo.git.execute(
        'git status --ignored --porcelain'.split(' ')
    ).splitlines()
    ignored_files = [
        _get_abs_path(repo.working_dir, entry[3:])
        for entry in status_files_with_ignored
        if entry.startswith('!!')
    ]

    return get_matching_entry(ignored_files, file_path) is not None


def get_versioned_files(root_path):
    repo = git.Repo(root_path)

    leaves = repo.git.execute('git ls-files'.split(' ')).splitlines()
    internal_nodes = repo.git.execute(
        'git ls-tree HEAD -d -r --name-only {}'.format(root_path).split(' ')
    ).splitlines()

    return [
        ",".join([root_path, relative_path])
        for relative_path in (internal_nodes + leaves)
    ]


def _get_abs_path(root_dir, entry):
    return "/".join([root_dir, entry])
