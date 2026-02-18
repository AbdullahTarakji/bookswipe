"""HTML email templates for BookSwipe notifications."""

from __future__ import annotations

BASE_STYLE = """
<style>
  body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
  .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; }
  .header { background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 32px 24px; text-align: center; }
  .header h1 { color: #ffffff; margin: 0; font-size: 24px; }
  .header p { color: #e0e7ff; margin: 8px 0 0; font-size: 14px; }
  .content { padding: 32px 24px; color: #374151; line-height: 1.6; }
  .content h2 { color: #1f2937; margin-top: 0; }
  .btn { display: inline-block; background: #6366f1; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; margin: 16px 0; }
  .book-card { background: #f9fafb; border-radius: 6px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #6366f1; }
  .book-card .title { font-weight: 600; color: #1f2937; }
  .book-card .author { color: #6b7280; font-size: 14px; }
  .stats { display: flex; gap: 16px; margin: 16px 0; }
  .stat-box { background: #f9fafb; border-radius: 6px; padding: 16px; text-align: center; flex: 1; }
  .stat-box .number { font-size: 28px; font-weight: 700; color: #6366f1; }
  .stat-box .label { color: #6b7280; font-size: 12px; text-transform: uppercase; }
  .footer { padding: 24px; text-align: center; color: #9ca3af; font-size: 12px; border-top: 1px solid #e5e7eb; }
  .footer a { color: #6366f1; }
  @media (max-width: 600px) { .container { border-radius: 0; } .content { padding: 24px 16px; } .stats { flex-direction: column; gap: 8px; } }
</style>
"""


def _wrap(body_html: str, app_url: str = "https://bookswipe.app") -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{BASE_STYLE}</head>
<body><div class="container">{body_html}
<div class="footer">
  <p>You're receiving this because you have a BookSwipe account.</p>
  <p><a href="{app_url}/settings/notifications">Manage email preferences</a> · <a href="{app_url}">Open BookSwipe</a></p>
</div></div></body></html>"""


def render_welcome(user_email: str, app_url: str = "https://bookswipe.app") -> tuple[str, str]:
    """Return (subject, html_body) for the welcome email."""
    subject = "Welcome to BookSwipe! 📚"
    html = _wrap(f"""
    <div class="header"><h1>📚 BookSwipe</h1><p>Discover your next favorite book</p></div>
    <div class="content">
      <h2>Welcome aboard!</h2>
      <p>Hi there! Thanks for joining BookSwipe. We're excited to help you discover amazing books tailored to your taste.</p>
      <p>Here's how to get started:</p>
      <ul>
        <li><strong>Swipe right</strong> on books you love</li>
        <li><strong>Swipe left</strong> to skip</li>
        <li>We'll learn your taste and recommend better books over time</li>
      </ul>
      <p style="text-align:center"><a class="btn" href="{app_url}">Start Swiping</a></p>
    </div>""", app_url)
    return subject, html


def render_weekly_digest(
    user_email: str,
    stats: dict,
    recommendations: list[dict],
    popular_books: list[dict],
    app_url: str = "https://bookswipe.app",
) -> tuple[str, str]:
    """Return (subject, html_body) for the weekly digest email.

    stats: {likes: int, skips: int, total_swipes: int}
    recommendations: [{title, authors}]
    popular_books: [{title, authors}]
    """
    subject = "Your Weekly BookSwipe Digest 📊"

    recs_html = ""
    for book in recommendations[:5]:
        recs_html += f'<div class="book-card"><div class="title">{book["title"]}</div><div class="author">{book.get("authors", "")}</div></div>'

    popular_html = ""
    for book in popular_books[:5]:
        popular_html += f'<div class="book-card"><div class="title">{book["title"]}</div><div class="author">{book.get("authors", "")}</div></div>'

    html = _wrap(f"""
    <div class="header"><h1>📊 Your Weekly Digest</h1><p>Here's what happened this week</p></div>
    <div class="content">
      <h2>Your Stats</h2>
      <table width="100%" cellpadding="0" cellspacing="8"><tr>
        <td style="background:#f9fafb;border-radius:6px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#6366f1">{stats.get("likes", 0)}</div>
          <div style="color:#6b7280;font-size:12px;text-transform:uppercase">Likes</div>
        </td>
        <td style="background:#f9fafb;border-radius:6px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#6366f1">{stats.get("skips", 0)}</div>
          <div style="color:#6b7280;font-size:12px;text-transform:uppercase">Skips</div>
        </td>
        <td style="background:#f9fafb;border-radius:6px;padding:16px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#6366f1">{stats.get("total_swipes", 0)}</div>
          <div style="color:#6b7280;font-size:12px;text-transform:uppercase">Total</div>
        </td>
      </tr></table>

      {"<h2>Recommended For You</h2>" + recs_html if recs_html else ""}
      {"<h2>Popular This Week</h2>" + popular_html if popular_html else ""}

      <p style="text-align:center"><a class="btn" href="{app_url}">Discover More</a></p>
    </div>""", app_url)
    return subject, html


def render_recommendation_alert(
    books: list[dict],
    app_url: str = "https://bookswipe.app",
) -> tuple[str, str]:
    """Return (subject, html_body) for a recommendation alert email.

    books: [{title, authors}]
    """
    subject = "New books matching your taste! 🎯"

    books_html = ""
    for book in books[:5]:
        books_html += f'<div class="book-card"><div class="title">{book["title"]}</div><div class="author">{book.get("authors", "")}</div></div>'

    html = _wrap(f"""
    <div class="header"><h1>🎯 New Matches</h1><p>Books we think you'll love</p></div>
    <div class="content">
      <h2>Fresh picks based on your taste</h2>
      <p>We found some new books that match your reading preferences:</p>
      {books_html}
      <p style="text-align:center"><a class="btn" href="{app_url}">Check Them Out</a></p>
    </div>""", app_url)
    return subject, html
