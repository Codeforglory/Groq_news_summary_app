from fastapi import FastAPI, Request
import jinja2
import pathlib
from datetime import datetime

# Using manual Jinja2 rendering to avoid TemplateResponse cache issues

from fastapi.responses import HTMLResponse, JSONResponse
import os

# Import the existing fetch function from news_app
try:
    from news_app import get_news as _raw_get_news
except Exception:
    _raw_get_news = None


def fetch_news(query: str = "Latest news on AI and technologies"):
    """Safely invoke the get_news tool or function from news_app.
    Handles wrapped/decorated tool objects by trying common attributes.
    Returns an empty list on failure.
    """
    if _raw_get_news is None:
        return []

    # Direct callable
    try:
        if callable(_raw_get_news):
            try:
                return _raw_get_news(query)
            except TypeError:
                return _raw_get_news()
    except Exception:
        pass

    # Try __wrapped__ (functools.wraps)
    wrapped = getattr(_raw_get_news, "__wrapped__", None)
    if callable(wrapped):
        try:
            return wrapped(query)
        except TypeError:
            try:
                return wrapped()
            except Exception:
                pass

    # Try common attributes used by tool wrappers
    func = getattr(_raw_get_news, "func", None)
    if callable(func):
        try:
            return func(query)
        except TypeError:
            try:
                return func()
            except Exception:
                pass

    for name in ("run", "call", "invoke"):
        method = getattr(_raw_get_news, name, None)
        if callable(method):
            try:
                return method(query)
            except TypeError:
                try:
                    return method()
                except Exception:
                    pass

    # Unknown structure -- fail gracefully
    return []

app = FastAPI(title="News Roundup")


def _format_published_date(value):
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.date().isoformat()

    text = str(value).strip()
    if not text:
        return ''

    if 'T' in text:
        text = text.split('T', 1)[0]
    elif ' ' in text:
        text = text.split(' ', 1)[0]

    return text


def summarize_articles(articles, top_n=5):
    summaries = []
    for a in (articles or [])[:top_n]:
        title = a.get('title') or a.get('name') or 'No title'
        description = a.get('description') or a.get('summary') or ''
        url = a.get('url') or a.get('link') or '#'
        published = _format_published_date(a.get('published') or a.get('published_date') or a.get('published_at') or '')
        summaries.append({'title': title, 'description': description, 'url': url, 'published': published})
    return summaries


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    try:
        articles = fetch_news()
    except Exception as e:
        return HTMLResponse(f"<h1>Error fetching news</h1><pre>{str(e)}</pre>", status_code=500)

    items = summarize_articles(articles)

    # Render template manually to avoid Jinja2 environment hashing issues
    tpl_path = pathlib.Path(__file__).parent / "templates" / "index.html"
    try:
        tpl_text = tpl_path.read_text(encoding="utf-8")
    except Exception as e:
        return HTMLResponse(f"<h1>Template load error</h1><pre>{str(e)}</pre>", status_code=500)

    tpl = jinja2.Template(tpl_text)
    content = tpl.render(items=items)
    return HTMLResponse(content)


@app.get("/api/news")
def api_news():
    try:
        articles = fetch_news()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse(summarize_articles(articles))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("news_web:app", host="0.0.0.0", port=8000, reload=True)
