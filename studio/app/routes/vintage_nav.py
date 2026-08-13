"""Shared navigation for Vintage Studio pages."""


def vintage_nav(current: str) -> str:
    evidence = "Evidence" if current == "evidence" else "Evidence"
    research = "Research" if current == "research" else "Research"
    return f"<nav><a href='/'>Studio</a> | <a href='/vintage-evidence'>{evidence}</a> | <a href='/vintage-research'>{research}</a></nav>"
