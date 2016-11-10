import argparse
import logging
import shlex
import subprocess
import sys
import time
from memory_profiler import profile

REPO = '/Users/weiapplatix/Documents/Work/projects/experiments/experiment_fetch/{}'
BRANCH = 'remotes/origin/{}'

logger = logging.getLogger(__name__)


@profile
def get_commits(repo, branch, sha=None, per_page=100):
    start_time = time.time()
    if not sha:
        # if sha is not supplied, we only need to retrieve `per_page` commits
        sha = get_branch_head(repo, branch)
        _per_page = per_page
    else:
        # if sha is supplied, the sha must be the last sha from previous page, then we need to retrieve `per_page + 1` commits
        _per_page = per_page + 1
    cmd = 'git -C {} rev-list {} --remotes={} --pretty=format:"%H,%an <%ae>,%aI,%cn <%ce>,%cI,%s" --max-count={}'.format(REPO.format(repo), sha, BRANCH.format(branch), per_page)
    try:
        cpi = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
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


@profile
def search_commits(repo, author=None, committer=None, description=None):
    start_time = time.time()
    cmd = 'git -C {} log --remotes --all --pretty=format:"%H,%an <%ae>,%aI,%cn <%ce>,%cI,%s"'.format(REPO.format(repo))
    if author:
        cmd += ' --author="{}"'.format(author)
    if committer:
        cmd += ' --committer="{}"'.format(committer)
    if description:
        cmd += ' --grep="{}"'.format(description)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commits = []
    for line in iter(proc.stdout.readline, b''):
        line = line[0:-1].decode(errors='replace')
        tokens = line.split(',')
        commit = {
            'commit': tokens[0],
            'author': tokens[1],
            'author_date': tokens[2],
            'committer': tokens[3],
            'commit_date': tokens[4],
            'description': ','.join(tokens[5:])
        }
        commits.append(commit)
    proc.stdout.close()
    proc.wait()
    logger.debug('Found %s commits', len(commits))
    end_time = time.time()
    logger.info('Operation completed in %s seconds', end_time - start_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    commits_parser = subparsers.add_parser('get_commits')
    commits_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')
    commits_parser.add_argument('--branch', action='store', dest='branch', required=True, type=str, help='specify name of branch')
    commits_parser.add_argument('--sha', action='store', dest='sha', default=None, type=str, help='specify sha of commit')
    commits_parser.add_argument('--per-page', action='store', dest='per_page', default=100, type=int, help='specify page size')

    search_parser = subparsers.add_parser('search_commits')
    search_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')
    search_parser.add_argument('--author', action='store', dest='author', default=None, type=str, help='specify name of branch')
    search_parser.add_argument('--committer', action='store', dest='committer', default=None, type=str, help='specify sha of commit')
    search_parser.add_argument('--description', action='store', dest='description', default=None, type=str, help='specify page size')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(threadName)s: %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.DEBUG)

    if args.command == 'get_commits':
        get_commits(args.repo, args.branch, args.sha, args.per_page)
    elif args.command == 'search_commits':
        search_commits(args.repo, args.author, args.committer, args.description)
