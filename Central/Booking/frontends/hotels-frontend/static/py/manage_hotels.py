from js import document, fetch, window
import json, asyncio
from pyodide.ffi import create_proxy

status_el = document.getElementById('status')
list_el = document.getElementById('managed-hotels')
loading_el = document.getElementById('loading')
empty_el = document.getElementById('empty')

API_LIST = '/api/hotels?managed=1'

def set_status(msg, kind='error'):
    if status_el:
        status_el.className = f'status show {kind}'
        status_el.textContent = msg

def clear_status():
    if status_el:
        status_el.className = 'status'
        status_el.textContent = ''

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
            list_el.hidden = False
            for h in hotels:
                card = render_hotel(h)
                list_el.appendChild(card)
    except Exception as e:
        set_status(f'Error: {e}', 'error')

def render_hotel(h):
    card = document.createElement('div')
    card.className = 'hotel-card'
    hid = h.get('hotel_id') or ''
    hidden_flag = h.get('hidden') is True
    img_url = h.get('image','')
    card.innerHTML = f'''<picture><img src="{img_url}" alt="{h.get('name','')}" loading="lazy" /></picture>
    <div class="hotel-body">
      <div class="hotel-name">{h.get('name','')} <span class="price">${h.get('price_per_night',0)}</span></div>
      <div class="meta">{h.get('city','')} • {h.get('country','')}</div>
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
