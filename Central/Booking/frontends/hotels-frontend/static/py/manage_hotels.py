from js import document, fetch, window
import json, asyncio, datetime
from pyodide.ffi import create_proxy

status_el = document.getElementById('status')
list_el = document.getElementById('managed-hotels')
loading_el = document.getElementById('loading')
empty_el = document.getElementById('empty')

API_LIST = '/api/hotels?managed=1'
API_AV = '/api/availability'

def set_status(msg, kind='error'):
    if status_el:
        status_el.className = f'status show {kind}'
        status_el.textContent = msg

def clear_status():
    if status_el:
        status_el.className = 'status'
        status_el.textContent = ''

def _date_iso(d):
    try:
        return d.isoformat()
    except Exception:
        return ''

def _default_range():
    today = datetime.date.today()
    end = today + datetime.timedelta(days=7)
    return today, end

async def load_hotels():
    try:
        r = await fetch(API_LIST)
        if not r.ok:
            set_status(f'Failed to load hotels ({r.status})', 'error')
            return
        data = await r.json()
        py = data.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Load failed'), 'error')
            return
        hotels = py.get('hotels') or []
        if loading_el:
            loading_el.remove()
        if not hotels:
            if empty_el:
                empty_el.hidden = False
            return
        if list_el:
            list_el.innerHTML = ''
            list_el.hidden = False
            # Determine date range
            avs = document.getElementById('av-start')
            ave = document.getElementById('av-end')
            if avs and ave:
                if not avs.value or not ave.value:
                    t, e = _default_range()
                    if avs and not avs.value:
                        avs.value = _date_iso(t)
                    if ave and not ave.value:
                        ave.value = _date_iso(e)
                start = avs.value
                end = ave.value
            else:
                t, e = _default_range()
                start = _date_iso(t)
                end = _date_iso(e)
            for h in hotels:
                card = await render_hotel(h, start, end)
                list_el.appendChild(card)
    except Exception as e:
        set_status(f'Error: {e}', 'error')

async def render_hotel(h, start, end):
    card = document.createElement('div')
    card.className = 'hotel-card'
    hid = h.get('hotel_id') or ''
    hidden_flag = h.get('hidden') is True
    img_url = h.get('image','')
    # Capacity placeholders, filled after availability fetch
    caps = '<div class="meta caps" style="margin-top:.4rem; display:flex; gap:.6rem; flex-wrap:wrap;">'
    rc = h.get('room_count', 0)
    caps += f'<span class="tag">Rooms: <strong>{rc}</strong></span>'
    caps += f'<span class="tag" id="b-{hid}">Booked: …</span>'
    caps += f'<span class="tag" id="a-{hid}">Available: …</span>'
    caps += '</div>'
    card.innerHTML = f'''<picture><img src="{img_url}" alt="{h.get('name','')}" loading="lazy" /></picture>
    <div class="hotel-body">
      <div class="hotel-name">{h.get('name','')} <span class="price">${h.get('price_per_night',0)}</span></div>
      <div class="meta">{h.get('city','')} • {h.get('country','')}</div>
      {caps}
      <div style="display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.4rem;">
        <a class="u-btn" href="/hotel/{hid}" style="text-decoration:none;">View</a>
        <a class="u-btn" href="/edit-hotel/{hid}" style="text-decoration:none;">Edit</a>
        <button class="u-btn" data-action="toggle" data-id="{hid}" style="background:{'#2b333e' if not hidden_flag else 'rgba(239,68,68,.12)'}; border-color:{'#303a46' if not hidden_flag else 'rgba(239,68,68,.4)'}; color:{'#e5e7eb' if not hidden_flag else '#fca5a5'};">{'Hide' if not hidden_flag else 'Unhide'}</button>
      </div>
      {('<div class="meta" style="margin-top:.5rem; color:#fca5a5;">Hidden</div>' if hidden_flag else '')}
    </div>'''
    # Attach events
    btns = card.getElementsByTagName('button')
    for i in range(btns.length):
        b = btns.item(i)
        if b.getAttribute('data-action') == 'toggle':
            b.addEventListener('click', create_proxy(lambda evt, bid=hid, node=b, c=card: asyncio.ensure_future(toggle_visibility(evt, bid, node, c))))
    # Fetch availability for the given date range
    try:
        params = f"?hotel_id={hid}&start={start}&end={end}"
        r = await fetch(f"{API_AV}{params}")
        if r.ok:
            data = await r.json()
            py = data.to_py()
            if py.get('ok'):
                # booked = max over range; available = min over range
                booked = py.get('max_booked', 0)
                avail = py.get('min_available', h.get('room_count', 0))
                b = card.querySelector(f"#b-{hid}")
                a = card.querySelector(f"#a-{hid}")
                if b:
                    b.textContent = f"Booked: {booked}"
                if a:
                    a.textContent = f"Available: {avail}"
        else:
            # Leave placeholders if API fails
            pass
    except Exception:
        pass
    return card

async def toggle_visibility(evt, hotel_id, btn, card):
    evt.preventDefault()
    if not hotel_id:
        return
    try:
        btn.disabled = True
        btn.textContent = '...'
        r = await fetch(f'/api/hotels/{hotel_id}/visibility', {
            'method':'PATCH',
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({})  # toggle
        })
        if not r.ok:
            btn.disabled = False
            btn.textContent = 'Retry'
            set_status(f'Visibility update failed ({r.status})','error')
            return
        data = await r.json()
        py = data.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Failed'),'error')
            btn.disabled=False
            btn.textContent='Retry'
            return
        hidden = py.get('hidden')
        # Re-render minimal changes
        if hidden:
            btn.textContent = 'Unhide'
            btn.style.background = 'rgba(239,68,68,.12)'
            btn.style.borderColor = 'rgba(239,68,68,.4)'
            btn.style.color = '#fca5a5'
            # Add hidden badge if absent
            badge = card.querySelector('.hidden-badge')
            if not badge:
                hb = document.createElement('div')
                hb.className = 'meta hidden-badge'
                hb.style.marginTop = '.5rem'
                hb.style.color = '#fca5a5'
                hb.textContent = 'Hidden'
                card.querySelector('.hotel-body').appendChild(hb)
        else:
            btn.textContent = 'Hide'
            btn.style.background = '#2b333e'
            btn.style.borderColor = '#303a46'
            btn.style.color = '#e5e7eb'
            badge = card.querySelector('.hidden-badge')
            if badge:
                badge.remove()
        set_status('Visibility updated','success')
        btn.disabled = False
    except Exception as e:
        set_status(f'Error: {e}','error')
        try:
            btn.disabled = False
        except Exception:
            pass

asyncio.ensure_future(load_hotels())

try:
    document.getElementById('year').textContent = str(__import__('datetime').datetime.now().year)
    document.getElementById('p-year').textContent = str(__import__('datetime').datetime.now().year)
except Exception:
    pass

# Wire refresh button and date validation
def _on_refresh(evt=None):
    asyncio.ensure_future(load_hotels())

btn = document.getElementById('btn-refresh')
if btn:
    btn.addEventListener('click', create_proxy(_on_refresh))

avs = document.getElementById('av-start')
ave = document.getElementById('av-end')
try:
    if avs and ave:
        today = datetime.date.today()
        avs.min = today.isoformat()
        # Ensure end > start
        def _sync_dates(evt=None):
            try:
                s = datetime.date.fromisoformat(avs.value) if avs.value else today
                e_min = s + datetime.timedelta(days=1)
                ave.min = e_min.isoformat()
                if ave.value:
                    e = datetime.date.fromisoformat(ave.value)
                    if e <= s:
                        ave.value = e_min.isoformat()
            except Exception:
                pass
        avs.addEventListener('change', create_proxy(_sync_dates))
        # Initialize defaults
        if not avs.value or not ave.value:
            s0, e0 = _default_range()
            if not avs.value:
                avs.value = _date_iso(s0)
            if not ave.value:
                ave.value = _date_iso(e0)
        _sync_dates()
except Exception:
    pass
