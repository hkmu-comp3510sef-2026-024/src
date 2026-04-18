from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "app" / "templates"
FRONTEND = ROOT / "frontend"

PAGE_MAP = {
    "public/home.html": "home/index.html",
    "auth/login.html": "login/index.html",
    "auth/register.html": "register/index.html",
    "public/catalog.html": "portal/index.html",
    "public/detail.html": "portal/detail/index.html",
    "member/portal.html": "member/index.html",
    "member/catalog.html": "member/catalog/index.html",
    "member/detail.html": "member/detail/index.html",
    "member/loans.html": "member/loans-page/index.html",
    "member/reservations.html": "member/reservations-page/index.html",
    "member/notifications.html": "member/notifications-page/index.html",
    "admin/portal.html": "admin/portal/index.html",
    "admin/members.html": "admin/members-page/index.html",
    "admin/books.html": "admin/books-page/index.html",
    "admin/copies.html": "admin/copies-page/index.html",
    "admin/circulation.html": "admin/circulation-page/index.html",
    "admin/fines.html": "admin/fines-page/index.html",
    "admin/auditlogs.html": "admin/auditlogs-page/index.html",
    "admin/reminder_policy.html": "admin/reminder-policy-page/index.html",
    "admin/reports.html": "admin/reports-page/index.html",
    "admin/users.html": "admin/users-page/index.html",
    "admin/announcements.html": "admin/announcements-page/index.html",
}


def extract_block(source: str, name: str) -> str:
    pattern = re.compile(r"{% block " + re.escape(name) + r" %}(.*?){% endblock %}", re.S)
    match = pattern.search(source)
    return match.group(1).strip() if match else ""


def render_page(title: str, page_class: str, content: str, scripts: str, current_path: str) -> str:
    def nav_class(prefix: str) -> str:
        return "is-active" if current_path == prefix or current_path.startswith(prefix + "/") else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title or "图书借阅与会员管理系统"}</title>
    <link rel="stylesheet" href="/static/assets/brand.css" />
  </head>
  <body class="">
    <header class="site-header">
      <div class="site-header__inner">
        <a class="brandmark" href="/">
          <span class="brandmark__icon" aria-hidden="true"></span>
          <span class="brandmark__copy">
            <strong>图书借阅与会员管理系统</strong>
            <small>馆藏检索与读者服务</small>
          </span>
        </a>

        <nav class="main-nav" aria-label="主导航">
          <a class="{nav_class('/')}" href="/">首页</a>
          <a class="{nav_class('/portal')}" href="/portal">馆藏检索</a>
          <a class="{nav_class('/member')}" href="/member">读者服务</a>
        </nav>

        <div class="header-actions">
          <div class="lang-switch" aria-label="Language switch">
            <button class="lang-switch__button" data-lang-switch="zh-CN" type="button">中文</button>
            <button class="lang-switch__button" data-lang-switch="en" type="button">EN</button>
          </div>
          <a id="access-entry" class="header-action" href="/login">登录/注册</a>
          <div id="account-menu" class="account-menu account-menu--hidden">
            <a id="member-entry" class="account-menu__item account-menu__item--hidden" href="/member">进入读者服务</a>
            <a id="admin-entry" class="account-menu__item account-menu__item--hidden" href="/admin/portal">进入管理后台</a>
            <button id="logout-entry" class="account-menu__item account-menu__button" type="button">退出登录</button>
          </div>
        </div>
      </div>
    </header>

    <div class="notice-bar">
      <div class="notice-bar__inner">
        <span id="notice-title" class="notice-bar__label" data-i18n-skip="true">公告</span>
        <p id="notice-message" data-i18n-skip="true">正在加载最新公告…</p>
      </div>
    </div>

    <main class="page {page_class}">
      {content}
    </main>

    <script>
      window.LibraryConfig = {{
        apiBase: 'http://localhost:23123'
      }};
    </script>
    <script src="/static/assets/i18n_runtime.js"></script>
    <script src="/static/assets/base_runtime.js"></script>
    <script>
      (async () => {{
        const i18n = window.LibraryI18n;
        const titleNode = document.getElementById('notice-title');
        const messageNode = document.getElementById('notice-message');
        let announcementMode = 'system';
        const defaultTitle = '开放时间提醒';
        const defaultMessage = '欢迎使用图书馆服务。借书、还书和预约办理请按页面提示操作。';
        function renderSystemNotice() {{
          titleNode.textContent = i18n.t(defaultTitle);
          messageNode.textContent = i18n.t(defaultMessage);
        }}
        if (!titleNode || !messageNode) return;
        titleNode.textContent = i18n.t('公告');
        messageNode.textContent = i18n.t('正在加载最新公告…');
        try {{
          const response = await fetch('/announcements/current');
          const payload = await response.json();
          if (payload?.data?.message) {{
            const nextTitle = payload?.data?.title || defaultTitle;
            const nextMessage = payload.data.message;
            announcementMode = nextTitle === defaultTitle && nextMessage === defaultMessage ? 'system' : 'custom';
            titleNode.textContent = announcementMode === 'system' ? i18n.t(defaultTitle) : nextTitle;
            messageNode.textContent = announcementMode === 'system' ? i18n.t(defaultMessage) : nextMessage;
          }} else {{
            renderSystemNotice();
          }}
        }} catch {{
          renderSystemNotice();
        }}
        window.addEventListener('library-lang-changed', () => {{
          if (announcementMode === 'system') {{
            renderSystemNotice();
          }}
        }});
      }})();
    </script>
    {scripts}
  </body>
</html>
"""


def output_path_to_route(path: str) -> str:
    route = "/" + Path(path).parent.as_posix()
    if route.endswith("/index"):
        route = route[: -len("/index")]
    if route == "/":
        return "/"
    return route


def main() -> None:
    FRONTEND.mkdir(parents=True, exist_ok=True)
    assets_target = FRONTEND / "static" / "assets"
    if assets_target.exists():
        shutil.rmtree(assets_target)
    assets_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATES / "assets", assets_target)

    for template_rel, output_rel in PAGE_MAP.items():
        source = (TEMPLATES / template_rel).read_text(encoding="utf-8")
        title = extract_block(source, "title")
        page_class = extract_block(source, "page_class")
        content = extract_block(source, "content")
        scripts = extract_block(source, "scripts")
        out_path = FRONTEND / output_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        route = output_path_to_route(output_rel)
        out_path.write_text(render_page(title, page_class, content, scripts, route), encoding="utf-8")

    # root page points to dedicated home
    home_html = (FRONTEND / "home" / "index.html").read_text(encoding="utf-8")
    (FRONTEND / "index.html").write_text(home_html, encoding="utf-8")


if __name__ == "__main__":
    main()
