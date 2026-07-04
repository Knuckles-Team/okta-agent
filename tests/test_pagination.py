"""CONCEPT:OK-OS.governance.okta Cursor pagination via Okta's Link rel="next" headers."""

import pytest

from tests.conftest import ORG_URL, RequestRecorder, json_response, link_next


@pytest.mark.concept("OK-OS.governance.okta")
class TestLinkHeaderPagination:
    def test_follows_next_links_and_aggregates(self, make_api):
        pages = {
            None: ([{"id": "u1"}, {"id": "u2"}], "c1"),
            "c1": ([{"id": "u3"}, {"id": "u4"}], "c2"),
            "c2": ([{"id": "u5"}], None),
        }

        def handler(request):
            after = request.url.params.get("after")
            items, next_cursor = pages[after]
            headers = link_next(next_cursor) if next_cursor else None
            return json_response(items, headers=headers)

        recorder = RequestRecorder(handler)
        result = make_api(recorder).list_users()
        assert [u["id"] for u in result["data"]] == ["u1", "u2", "u3", "u4", "u5"]
        assert result["count"] == 5
        assert result["truncated"] is False
        assert result["next_cursor"] is None
        assert len(recorder.requests) == 3

    def test_next_url_from_link_header_is_followed_verbatim(self, make_api):
        def handler(request):
            if request.url.params.get("after") == "c1":
                return json_response([{"id": "u2"}])
            return json_response([{"id": "u1"}], headers=link_next("c1"))

        recorder = RequestRecorder(handler)
        make_api(recorder).list_users(q="alice")
        second = recorder.requests[1]
        assert str(second.url).startswith(f"{ORG_URL}/api/v1/users")
        assert second.url.params["after"] == "c1"
        # the next URL replaces the original query entirely (Okta carries it)
        assert "q" not in second.url.params

    def test_max_items_truncates_and_reports_cursor(self, make_api):
        def handler(request):
            return json_response(
                [{"id": f"u{i}"} for i in range(5)], headers=link_next("c-more")
            )

        result = make_api(handler).list_users(max_items=3)
        assert result["count"] == 3
        assert result["truncated"] is True
        assert result["next_cursor"] == "c-more"

    def test_single_page_without_link_header(self, make_api):
        result = make_api(lambda request: json_response([{"id": "g1"}])).list_groups()
        assert result["count"] == 1
        assert result["truncated"] is False
        assert result["next_cursor"] is None

    def test_exact_max_items_with_no_next_page_not_truncated(self, make_api):
        result = make_api(
            lambda request: json_response([{"id": "u1"}, {"id": "u2"}])
        ).list_users(max_items=2)
        assert result["count"] == 2
        assert result["truncated"] is False
