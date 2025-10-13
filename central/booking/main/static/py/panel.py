from js import document, fetch
import asyncio, datetime
from pyodide.ffi import create_proxy

FOCUSABLE_SELECTOR = 'a[href], button:not([disabled]), [tabindex="0"]'
_last_focus = { 'el': None }

# Elements (lazy looked up in init)
nav_toggle = None
side_panel = None
panel_overlay = None
panel_close = None
logout_btn_header = None
logout_btn_panel = None

async def _do_logout(btn):
    if not btn:
        return
    original = btn.textContent
    btn.disabled = True
    btn.textContent = 'Logging out…'
    try:
        resp = await fetch('/logout', { 'method': 'POST', 'headers': { 'Accept': 'application/json' } })
        if getattr(resp, 'ok', False):
            from js import window
            window.location.href = '/'
            return
    except Exception:
        pass
    btn.textContent = 'Retry'
    btn.disabled = False
    async def restore():
        await asyncio.sleep(3)
        if not btn.disabled:
            btn.textContent = original
    asyncio.ensure_future(restore())

def open_panel():
    if not side_panel:
        return
    _last_focus['el'] = document.activeElement
    side_panel.classList.add('open')
    if panel_overlay:
        panel_overlay.classList.add('show')
        panel_overlay.hidden = False
    if nav_toggle:
        nav_toggle.setAttribute('aria-expanded', 'true')
    side_panel.setAttribute('aria-hidden', 'false')
    def focus_first():
        try:
            first = side_panel.querySelector(FOCUSABLE_SELECTOR)
            if first:
                first.focus()
        except Exception:
            pass
    asyncio.ensure_future(asyncio.sleep(0))
    focus_first()
    document.addEventListener('keydown', _key_handler_proxy)

def close_panel():
    if not side_panel:
        return
    side_panel.classList.remove('open')
    if panel_overlay:
        panel_overlay.classList.remove('show')
        panel_overlay.hidden = True
    if nav_toggle:
        nav_toggle.setAttribute('aria-expanded', 'false')
    side_panel.setAttribute('aria-hidden', 'true')
    document.removeEventListener('keydown', _key_handler_proxy)
    try:
        lf = _last_focus.get('el')
        if lf:
            lf.focus()
    except Exception:
        pass

def _handle_key(evt):
    try:
        key = evt.key
        if key == 'Escape':
            close_panel(); return
        if key == 'Tab' and side_panel and side_panel.classList.contains('open'):
            focusables = side_panel.querySelectorAll(FOCUSABLE_SELECTOR)
            if not focusables.length:
                return
            first = focusables.item(0)
            last = focusables.item(focusables.length - 1)
            active = document.activeElement
            if evt.shiftKey and active == first:
                evt.preventDefault(); last.focus()
            elif (not evt.shiftKey) and active == last:
                evt.preventDefault(); first.focus()
    except Exception:
        pass

_key_handler_proxy = create_proxy(_handle_key)

def _toggle_click(evt):
    if side_panel and side_panel.classList.contains('open'):
        close_panel()
    else:
        open_panel()

def _overlay_click(evt):
    close_panel()

def _close_click(evt):
    close_panel()

def _logout_header(evt):
    from js import event
    asyncio.ensure_future(_do_logout(logout_btn_header))

def _logout_panel(evt):
    asyncio.ensure_future(_do_logout(logout_btn_panel))

def init_panel():
    global nav_toggle, side_panel, panel_overlay, panel_close, logout_btn_header, logout_btn_panel
    nav_toggle = document.getElementById('nav-toggle')
    side_panel = document.getElementById('side-panel')
    panel_overlay = document.getElementById('panel-overlay')
    panel_close = document.getElementById('panel-close')
    logout_btn_header = document.getElementById('logout-btn')
    logout_btn_panel = document.getElementById('panel-logout')

    if nav_toggle:
        nav_toggle.addEventListener('click', create_proxy(_toggle_click))
    if panel_overlay:
        panel_overlay.addEventListener('click', create_proxy(_overlay_click))
    if panel_close:
        panel_close.addEventListener('click', create_proxy(_close_click))
    if logout_btn_header:
        logout_btn_header.addEventListener('click', create_proxy(lambda e: asyncio.ensure_future(_do_logout(logout_btn_header))))
    if logout_btn_panel:
        logout_btn_panel.addEventListener('click', create_proxy(lambda e: asyncio.ensure_future(_do_logout(logout_btn_panel))))

    # Set side panel year if present
    try:
        py = document.getElementById('p-year')
        if py:
            py.textContent = str(datetime.datetime.now().year)
    except Exception:
        pass

    from js import window
    window.addEventListener('pageshow', create_proxy(lambda e: close_panel()))

async def _deferred_init():
    await asyncio.sleep(0)
    init_panel()

asyncio.ensure_future(_deferred_init())
