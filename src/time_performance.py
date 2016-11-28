import argparse
import concurrent.futures
import logging
import shlex
import subprocess
import sys
import time

REPO = '/Users/weiapplatix/Documents/Work/projects/experiments/experiment_fetch/{}'
BRANCH = 'remotes/origin/{}'

logger = logging.getLogger(__name__)


def get_branches(repo):
    start_time = time.time()
    cmd = 'git -C {} branch --remote --all'.format(REPO.format(repo))
    try:
        cpi = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        stdout = cpi.stdout.decode(errors='replace')
        branches = [line.lstrip().replace('remotes/origin/', '') for line in stdout.split('\n') if line]
        logger.debug('Found %s branches', len(branches))
        return branches
    finally:
        end_time = time.time()
        logger.info('Operation completed in %s seconds', end_time - start_time)


def get_commits(repo, branch, sha=None, per_page=100):
    start_time = time.time()
    if not sha:
        # if sha is not supplied, we only need to retrieve `per_page` commits
        sha = get_branch_head(repo, branch)
        _per_page = per_page
    else:
        # if sha is supplied, the sha must be the last sha from previous page, then we need to retrieve `per_page + 1` commits
        _per_page = per_page + 1
    cmd = 'git -C {} rev-list {} --remotes={} --pretty=format:"%H,%an <%ae>,%aI,%cn <%ce>,%cI,%s" --skip=300 --max-count={}'.format(REPO.format(repo), sha, BRANCH.format(branch), per_page)
    try:
        cpi = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        lines = cpi.stdout.decode(errors='replace').split('\n')
        commits = []
        start = 1 if _per_page == per_page else 3
        for i in range(start, len(lines), 2):
            if not lines[i]:
                continue
            tokens = lines[i].split(',')
            commit = {
                'commit': tokens[0],
                'author': tokens[1],
                'author_date': tokens[2],
                'committer': tokens[3],
                'commit_date': tokens[4],
                'description': ','.join(tokens[5:])
            }
            commits.append(commit)
        logger.debug('Found %s commits on branch %s', len(commits), branch)
        for i in range(len(commits)):
            logger.debug(' * %s', commits[i]['commit'])
        return commits
    finally:
        end_time = time.time()
        logger.info('Operation completed in %s seconds', end_time - start_time)


def get_branch_head(repo, branch):
    cmd = 'git -C {} rev-parse {}'.format(REPO.format(repo), BRANCH.format(branch))
    try:
        cpi = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        stdout = cpi.stdout.decode(errors='replace')
        branch_head = stdout.strip()
        logger.debug('The branch head is: %s', branch_head)
        return branch_head


def get_commit(repo, sha):
    start_time = time.time()
    cmd = 'git -C {} show {} --quiet --pretty=format:"%H,%an <%ae>,%aI,%cn <%ce>,%cI,%s"'.format(REPO.format(repo), sha)
    try:
        cpi = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        stdout = cpi.stdout.decode(errors='replace')
        tokens = stdout.strip().split(',')
        commit = {
            'commit': tokens[0],
            'author': tokens[1],
            'author_date': tokens[2],
            'committer': tokens[3],
            'commit_date': tokens[4],
            'description': ','.join(tokens[5:])
        }
        logger.debug('Retrieved metadata of commit %s', sha)
        return commit
    finally:
        end_time = time.time()
        logger.info('Operation completed in %s seconds', end_time - start_time)


def search_commits(repo, author=None, committer=None, description=None):
    start_time = time.time()
    cmd = 'git fetch && git -C {} log --remotes --all --pretty=format:"%H,%an <%ae>,%aI,%cn <%ce>,%cI,%s"'.format(REPO.format(repo))
    if author:
        cmd += ' --author="{}"'.format(author)
    if committer:
        cmd += ' --committer="{}"'.format(committer)
    if description:
        cmd += ' --grep="{}"'.format(description)
    try:
        cpi = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        lines = cpi.stdout.decode(errors='replace').split('\n')
        commits = []
        for i in range(len(lines)):
            if not lines[i]:
                continue
            tokens = lines[i].split(',')
            commit = {
                'commit': tokens[0],
                'author': tokens[1],
                'author_date': tokens[2],
                'committer': tokens[3],
                'commit_date': tokens[4],
                'description': ','.join(tokens[5:])
            }
            commits.append(commit)
        logger.debug('Found %s commits', len(commits))
        # for i in range(len(commits)):
        #     logger.debug(' * %s', commits[i]['commit'])
        return commits
    finally:
        end_time = time.time()
        logger.info('Operation completed in %s seconds', end_time - start_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    branches_parser = subparsers.add_parser('get_branches')
    branches_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')

    commits_parser = subparsers.add_parser('get_commits')
    commits_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')
    commits_parser.add_argument('--branch', action='store', dest='branch', required=True, type=str, help='specify name of branch')
    commits_parser.add_argument('--sha', action='store', dest='sha', default=None, type=str, help='specify sha of commit')
    commits_parser.add_argument('--per-page', action='store', dest='per_page', default=100, type=int, help='specify page size')

    commit_parser = subparsers.add_parser('get_commit')
    commit_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')
    commit_parser.add_argument('--branch', action='store', dest='branch', required=True, type=str, help='specify name of branch')

    search_parser = subparsers.add_parser('search_commits')
    search_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')
    search_parser.add_argument('--author', action='store', dest='author', default=None, type=str, help='specify name of branch')
    search_parser.add_argument('--committer', action='store', dest='committer', default=None, type=str, help='specify sha of commit')
    search_parser.add_argument('--description', action='store', dest='description', default=None, type=str, help='specify page size')

    concurrent_search_parser = subparsers.add_parser('concurrent_search_commits')
    concurrent_search_parser.add_argument('--concurrency', action='store', dest='concurrency', required=True, type=int, help='specify concurrency')
    concurrent_search_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')
    concurrent_search_parser.add_argument('--author', action='store', dest='author', default=None, type=str, help='specify name of branch')
    concurrent_search_parser.add_argument('--committer', action='store', dest='committer', default=None, type=str, help='specify sha of commit')
    concurrent_search_parser.add_argument('--description', action='store', dest='description', default=None, type=str, help='specify page size')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(threadName)s: %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.DEBUG)

    if args.command == 'get_branches':
        get_branches(args.repo)
    elif args.command == 'get_commits':
        get_commits(args.repo, args.branch, args.sha, args.per_page)
    elif args.command == 'get_commit':
        sha = get_branch_head(args.repo, args.branch)
        get_commit(args.repo, sha)
    elif args.command == 'search_commits':
        search_commits(args.repo, args.author, args.committer, args.description)
    else:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for _ in range(args.concurrency):
                executor.submit(search_commits, args.repo, args.author, args.committer, args.description)
