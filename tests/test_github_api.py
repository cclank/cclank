"""Tests for GitHub API data aggregation."""

from generator.github_api import GitHubAPI


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.headers = {}
        self.status_code = 200
        self.text = ""

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def graphql_payload(stars, has_next_page=False, end_cursor=None, total_count=101):
    return {
        "data": {
            "user": {
                "pullRequests": {"totalCount": 7},
                "issues": {"totalCount": 3},
                "repositories": {
                    "totalCount": total_count,
                    "pageInfo": {
                        "hasNextPage": has_next_page,
                        "endCursor": end_cursor,
                    },
                    "nodes": [{"stargazerCount": count} for count in stars],
                },
                "contributionsCollection": {
                    "totalCommitContributions": 11,
                    "restrictedContributionsCount": 2,
                },
            }
        }
    }


def test_graphql_stats_paginates_repositories(monkeypatch):
    api = GitHubAPI("galaxy-dev", token="token")
    responses = [
        FakeResponse(graphql_payload([100, 200], has_next_page=True, end_cursor="cursor-1")),
        FakeResponse(graphql_payload([300], has_next_page=False)),
    ]
    variables = []

    def fake_request(method, url, **kwargs):
        variables.append(kwargs["json"]["variables"])
        return responses.pop(0)

    monkeypatch.setattr(api, "_request", fake_request)

    stats = api._fetch_stats_graphql()

    assert stats == {
        "commits": 13,
        "stars": 600,
        "prs": 7,
        "issues": 3,
        "repos": 101,
    }
    assert variables == [
        {"username": "galaxy-dev", "repoCursor": None},
        {"username": "galaxy-dev", "repoCursor": "cursor-1"},
    ]
