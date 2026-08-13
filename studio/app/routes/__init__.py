"""HTTP routers."""

# main.py still imports vintage_design_page; bind that name to the replacement
# research workbench so the obsolete module is no longer mounted.
from app.routes import vintage_research_mount as vintage_design_page

# Re-exported deliberately: main.py imports this name from the package.
__all__ = ["vintage_design_page"]
