import argparse
import json
import logging
import redis
import subprocess
import sys
import time

REPO = '/Users/weiapplatix/Documents/Work/projects/experiments/experiment_fetch/{}'
BRANCH = 'remotes/origin/{}'

logger = logging.getLogger(__name__)
redis_client = redis.StrictRedis(encoding_errors='replace', decode_responses=True)


def get_branches(repo):
    start_time = time.time()
    cmd = 'git -C {} branch --remote'.format(REPO.format(repo))
    try:
        cpi = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        stdout = cpi.stdout.decode(errors='replace')
        branches = [line.lstrip().replace('origin/', '') for line in stdout.split('\n') if line]
        logger.debug('Found %s branches', len(branches))
        return branches
    finally:
        end_time = time.time()
        logger.info('Operation completed in %s seconds', end_time - start_time)


def get_commits(repo, branch):
    start_time = time.time()
    sha = get_branch_head(repo, branch)
    cmd = 'git -C {} rev-list {} --remotes={} --pretty=format:"%H,%an <%ae>,%aI,%cn <%ce>,%cI,%s"'.format(
        REPO.format(repo), sha, BRANCH.format(branch))
    try:
        cpi = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
    else:
        lines = cpi.stdout.decode(errors='replace').split('\n')
        commits = []
        for i in range(1, len(lines), 2):
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
        redis_client.set('({}, {})'.format(repo, branch), json.dumps(commits))
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    write_cache_parser = subparsers.add_parser('write_cache')
    write_cache_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')

    read_cache_parser = subparsers.add_parser('read_cache')
    read_cache_parser.add_argument('--repo', action='store', dest='repo', required=True, type=str, help='specify name of repo')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(threadName)s: %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        stream=sys.stdout,
                        level=logging.DEBUG)

    if args.command == 'write_cache':
        branches = get_branches(args.repo)
        if 'master' in branches:
            get_commits(args.repo, 'master')
        elif 'trunk' in branches:
            get_commits(args.repo, 'trunk')
        else:
            get_commits(args.repo, branches[0])
    else:
        branches = get_branches(args.repo)
        if 'master' in branches:
            branch = 'master'
        elif 'trunk' in branches:
            branch = 'trunk'
        else:
            branch = branches[0]
        start_time = time.time()
        commits = json.loads(redis_client.get('({}, {})'.format(args.repo, branch)))
        end_time = time.time()
        logger.info('Read %s commits in %s seconds', len(commits), end_time - start_time)
