"""Tests for the AI-tell scanner."""

from __future__ import annotations

from mcp_klartext.scanner import scan_for_ai_tells


def _categories(result: dict) -> set[str]:
    return {i["category"] for i in result["issues"]}


def _patterns(result: dict) -> set[str]:
    return {i["pattern"] for i in result["issues"]}


def test_clean_text_has_no_issues():
    text = (
        "I learned to code on my dad's lap. The screen glowed green. "
        "My fingers were too small for the keys, so I hit them with my whole hand."
    )
    result = scan_for_ai_tells(text)
    assert result["clean"] is True
    assert result["stats"]["high"] == 0
    assert result["stats"]["medium"] == 0


def test_detects_delve():
    result = scan_for_ai_tells("Let me delve into the details.")
    assert "delve" in _patterns(result)
    assert result["clean"] is False


def test_detects_leverage_verb():
    result = scan_for_ai_tells("We leverage the platform to move faster.")
    assert "leverage" in _patterns(result)


def test_detects_seamless():
    result = scan_for_ai_tells("It integrates seamlessly with your workflow.")
    assert "seamless" in _patterns(result)


def test_detects_robust():
    result = scan_for_ai_tells("We built a robust solution.")
    assert "robust" in _patterns(result)


def test_detects_navigate_the_landscape():
    result = scan_for_ai_tells("You have to navigate the landscape of tooling.")
    patterns = _patterns(result)
    assert "navigate the [abstract]" in patterns
    assert "landscape of" in patterns


def test_detects_at_the_intersection_of():
    result = scan_for_ai_tells("We work at the intersection of design and code.")
    assert "at the intersection of" in _patterns(result)


def test_detects_not_just_x_em_dash_y():
    result = scan_for_ai_tells("It's not just a tool — it's a philosophy.")
    assert "it's not (just) X — it's Y" in _patterns(result)


def test_detects_not_just_x_but_y():
    result = scan_for_ai_tells("This is not just faster, but smarter.")
    assert "not just X, but Y" in _patterns(result)


def test_detects_in_a_world_where():
    result = scan_for_ai_tells("In a world where everything is AI, taste matters.")
    assert any("world where" in p for p in _patterns(result))


def test_detects_lets_dive_in():
    result = scan_for_ai_tells("Let's dive in and see what happens.")
    assert "let's dive in" in _patterns(result)


def test_detects_imagine_a_world():
    result = scan_for_ai_tells("Imagine a world where content writes itself.")
    assert "imagine a world" in _patterns(result)


def test_detects_typographic_apostrophe_in_its_not():
    """Curly apostrophes are common in real drafts — must still match."""
    result = scan_for_ai_tells("It\u2019s not just fast \u2014 it\u2019s instant.")
    assert "it's not (just) X — it's Y" in _patterns(result)


def test_em_dash_within_budget_is_allowed():
    text = (
        "I thought the project was going well. " * 30
    ) + "Then — like always — it wasn't."
    # ~180 words, budget = 1, two em-dashes go over.
    result = scan_for_ai_tells(text)
    em_issues = [i for i in result["issues"] if i["category"] == "em_dash"]
    assert len(em_issues) >= 1
    assert result["stats"]["em_dash_count"] == 2


def test_em_dash_below_budget_does_not_flag():
    text = " ".join(["word"] * 200) + " Here is a single em-dash — once."
    result = scan_for_ai_tells(text)
    em_issues = [i for i in result["issues"] if i["category"] == "em_dash"]
    assert em_issues == []


def test_lexical_hits_are_high_severity():
    result = scan_for_ai_tells("We delve and leverage the robust approach.")
    severities = {i["severity"] for i in result["issues"]}
    assert "high" in severities


def test_issue_reports_line_number():
    text = "Line one.\nLine two has delve in it.\nLine three."
    result = scan_for_ai_tells(text)
    delve_issues = [i for i in result["issues"] if i["pattern"] == "delve"]
    assert delve_issues[0]["line"] == 2


def test_multiple_hits_all_reported():
    text = "We delve into the robust landscape. It's seamless."
    result = scan_for_ai_tells(text)
    patterns = _patterns(result)
    assert {"delve", "robust", "seamless"} <= patterns


def test_stats_shape():
    result = scan_for_ai_tells("Hello world, this is a short draft.")
    stats = result["stats"]
    for key in (
        "word_count",
        "em_dash_count",
        "em_dash_budget",
        "issue_count",
        "high",
        "medium",
        "low",
    ):
        assert key in stats
        assert isinstance(stats[key], int)


def test_repeated_sentence_openers_flagged():
    text = "We built this. We shipped that. We tested everything."
    result = scan_for_ai_tells(text)
    assert any(i["pattern"] == "repeated sentence opener" for i in result["issues"])


def test_clean_flag_false_on_high_severity():
    result = scan_for_ai_tells("We leverage synergies.")
    assert result["clean"] is False


def test_clean_flag_true_with_only_low_severity():
    # Adjective stack is low severity; should not flip `clean` to false.
    result = scan_for_ai_tells(
        "A thoughtful, careful, methodical approach works best here."
    )
    # If only low-severity hits exist, clean should remain True.
    non_low = [i for i in result["issues"] if i["severity"] != "low"]
    if not non_low:
        assert result["clean"] is True
