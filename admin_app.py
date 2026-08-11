from fastapi.responses import HTMLResponse

from admin_ui import ADMIN_HTML
from server import app


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard():
    return ADMIN_HTML
