"""
Bitbucket Bulk Branch Creator Script
====================================

This async Python script interacts with the Bitbucket REST API to:
1. Fetch all repositories from a given workspace.
2. Check if a specific source branch exists in each repository.
3. If it exists, create a new branch from that source branch.

Useful for automating tasks like bulk cloning or replicating a branch across all repositories in an organization.

Requirements:
- aiohttp
- aiofiles

Note: Be sure to replace configuration values with your own before running.

Author: [Your Name]
License: MIT
"""

import asyncio
import aiohttp
from aiohttp import BasicAuth
import aiofiles

# === CONFIGURATION ===
WORKSPACE = ''            # Bitbucket workspace ID (e.g., 'adobe', 'cisco')
USERNAME = ''             # Bitbucket username
APP_PASSWORD = ''         # Bitbucket app password (generate from Bitbucket settings)
HEADERS = {'Content-Type': 'application/json'}
BASE_URL = 'https://api.bitbucket.org/2.0'
REPO_LOG_FILE = 'all_repos.txt'
MAX_CONCURRENT_REQUESTS = 50  # Limit concurrent requests to avoid rate-limiting

# === Auth and Throttling ===
auth = BasicAuth(USERNAME, APP_PASSWORD)
sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# === Utility Functions ===

async def fetch_json(session, url):
    """Fetch JSON data from a given Bitbucket API URL."""
    async with sem:
        async with session.get(url, auth=auth) as resp:
            if resp.status != 200:
                print(f"Failed to fetch {url}: {resp.status}")
                return None
            return await resp.json()

async def get_all_repositories(session):
    """Fetch all repositories in the workspace."""
    repos = []
    url = f"{BASE_URL}/repositories/{WORKSPACE}"
    while url:
        data = await fetch_json(session, url)
        if not data:
            break
        repos.extend(data.get('values', []))
        url = data.get('next')
    return repos

async def get_branch_info(session, repo_slug, branch_name):
    """Check if the source branch exists in a repository."""
    url = f"{BASE_URL}/repositories/{WORKSPACE}/{repo_slug}/refs/branches/{branch_name}"
    async with sem:
        async with session.get(url, auth=auth) as resp:
            if resp.status == 200:
                return await resp.json()
            return None

async def create_branch(session, repo_slug, new_branch, source_branch_info):
    """Create a new branch from the specified source branch info."""
    source_hash = source_branch_info['target']['hash']
    url = f"{BASE_URL}/repositories/{WORKSPACE}/{repo_slug}/refs/branches"
    payload = {
        "name": new_branch,
        "target": {
            "hash": source_hash
        }
    }

    async with sem:
        async with session.post(url, json=payload, auth=auth) as resp:
            text = await resp.text()
            if resp.status == 201:
                print(f"Branch '{new_branch}' created in {repo_slug}")
            elif resp.status == 400 and "already exists" in text:
                print(f"Branch '{new_branch}' already exists in {repo_slug}")
            else:
                print(f"Failed to create branch in {repo_slug}: {resp.status} - {text}")

async def process_repo(session, repo):
    """Process a single repository: check for source branch and create a new one."""
    repo_slug = repo['slug']
    print(f"\nProcessing repository: {repo_slug}")

    source_branch_name = ''  # Replace with your actual source branch name (e.g., 'main')
    new_branch_name = ''     # Replace with your desired new branch name (e.g., 'main-copy')

    source_branch_info = await get_branch_info(session, repo_slug, source_branch_name)

    if source_branch_info:
        await create_branch(session, repo_slug, new_branch_name, source_branch_info)
    else:
        print(f"Source branch '{source_branch_name}' not found in {repo_slug}, skipping.")

# === Main Execution ===

async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        print("Fetching repositories...")
        repos = await get_all_repositories(session)
        print(f"Found {len(repos)} repositories.")

        # Log all repository slugs
        async with aiofiles.open(REPO_LOG_FILE, 'w') as f:
            await f.write('\n'.join([r['slug'] for r in repos]))

        # Start processing repositories
        tasks = [process_repo(session, repo) for repo in repos]
        await asyncio.gather(*tasks)

# Entry point
if __name__ == '__main__':
    asyncio.run(main())
