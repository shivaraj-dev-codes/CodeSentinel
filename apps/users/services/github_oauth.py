"""GitHub OAuth service — exchange code for token and fetch user profile."""
import requests
from django.conf import settings


def exchange_github_code(code: str) -> str:
    """
    Exchange a temporary GitHub OAuth code for a persistent access token.
    Raises ValueError if the exchange fails.
    """
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        json={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_CALLBACK_URL,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

    return data["access_token"]


def fetch_github_user(token: str) -> dict:
    """
    Fetch the authenticated GitHub user's profile using their access token.
    Returns a dict with login, avatar_url, name, email, etc.
    """
    response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def fetch_github_repos(token: str) -> list[dict]:
    """
    Fetch all repositories the authenticated user has access to.
    Handles pagination automatically.
    """
    repos = []
    url = "https://api.github.com/user/repos"
    params = {"per_page": 100, "sort": "updated", "type": "all"}

    while url:
        response = requests.get(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        repos.extend(response.json())

        # Follow pagination links
        link_header = response.headers.get("Link", "")
        next_url = None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
                break
        url = next_url
        params = {}  # params are baked into the next URL

    return repos
