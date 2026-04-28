import importlib


def _get_scout_module():
    return importlib.import_module("operator_dashboard.web_trigger_scout")


def test_official_result_found_returns_review_action():
    mod = _get_scout_module()

    def fake_search(_query):
        return ["https://www.ufc.com/news/jafel-filho-vs-cody-durden-results"]

    def fake_fetch(_url):
        return "Cody Durden def. Jafel Filho by decision in Round 3 at 5:00."

    scout = mod.WebTriggerScout(search_provider=fake_search, page_fetcher=fake_fetch)
    result = scout.run(query="check Jafel Filho vs Cody Durden result")
    row = result["results"][0]

    assert result["ok"] is True
    assert row["trigger_type"] == "OFFICIAL_RESULT_FOUND"
    assert row["winner"] == "Cody Durden"
    assert row["recommended_action"] == "RESULT_READY_FOR_REVIEW"


def test_identity_conflict_returns_manual_identity_review():
    mod = _get_scout_module()

    def fake_search(_query):
        return ["https://www.tapology.com/fightcenter/events/123"]

    def fake_fetch(_url):
        return "Alan Chaves defeated Miguel Madueno by decision."

    scout = mod.WebTriggerScout(search_provider=fake_search, page_fetcher=fake_fetch)
    result = scout.run(query="verify Abel Chaves vs Miguel Madueno")
    row = result["results"][0]

    assert row["trigger_type"] == "IDENTITY_CONFLICT"
    assert row["recommended_action"] == "IDENTITY_CONFLICT_REVIEW"


def test_conflicting_sources_return_source_conflict():
    mod = _get_scout_module()
    pages = {
        "https://www.ufc.com/a": "Fighter One def. Fighter Two by KO in Round 2 1:10",
        "https://www.espn.com/b": "Fighter Two def. Fighter One by decision in Round 3 5:00",
    }

    def fake_search(_query):
        return list(pages.keys())

    def fake_fetch(url):
        return pages[url]

    scout = mod.WebTriggerScout(search_provider=fake_search, page_fetcher=fake_fetch)
    result = scout.run(query="check Fighter One vs Fighter Two result")
    row = result["results"][0]

    assert row["trigger_type"] == "SOURCE_CONFLICT"
    assert row["recommended_action"] == "MANUAL_REVIEW_REQUIRED"


def test_secondary_result_is_marked_non_official():
    mod = _get_scout_module()

    def fake_search(_query):
        return ["https://www.tapology.com/fightcenter/fights/abc"]

    def fake_fetch(_url):
        return "Cody Durden defeated Jafel Filho via submission in round 2 at 2:33"

    scout = mod.WebTriggerScout(search_provider=fake_search, page_fetcher=fake_fetch)
    result = scout.run(query="check Jafel Filho vs Cody Durden result")
    row = result["results"][0]

    assert row["trigger_type"] == "SECONDARY_RESULT_FOUND"
    assert row["source_confidence"] == "secondary"
    assert row["recommended_action"] == "SOURCE_NOT_OFFICIAL"


def test_read_only_blocked_actions_are_returned():
    mod = _get_scout_module()

    def fake_search(_query):
        return []

    def fake_fetch(_url):
        return ""

    scout = mod.WebTriggerScout(search_provider=fake_search, page_fetcher=fake_fetch)
    result = scout.run(query="search web for fight results")

    assert "No ledger mutation performed" in result["blocked_actions"]
    assert "No prediction mutation performed" in result["blocked_actions"]
    assert "No structural backfill applied" in result["blocked_actions"]
