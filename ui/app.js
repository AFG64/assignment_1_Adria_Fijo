/* Static Picky collection UI. Restaurant and dining addresses come only from config.js. */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const content = $('#content');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const statuses = {want_to_go: 'Want to go', visited: 'Visited', not_saved: 'Not saved'};
  let generation = 0, lastList = '#/saved', busy = false;
  let pending = [];
  try { pending = JSON.parse(localStorage.getItem('picky-cleanup') || sessionStorage.getItem('picky-cleanup') || '[]').filter(row => Number.isInteger(row.id) && row.id > 0 && row.id <= 2147483647 && typeof row.title === 'string'); localStorage.setItem('picky-cleanup', JSON.stringify(pending)); sessionStorage.removeItem('picky-cleanup'); } catch { /* Storage can be disabled; current-session memory still works. */ }

  function notice(message) {
    $('#notice').textContent = message;
    $('#notice').hidden = !message;
  }

  async function api(domain, path, {method = 'GET', body, download = false, uncertain} = {}) {
    const config = window.PICKY_CONFIG || {};
    const base = config[domain];
    try {
      const url = new URL(base);
      if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || (location.protocol === 'https:' && url.protocol !== 'https:')) throw new Error();
    } catch { throw new Error('Picky is not ready to connect. Please check with the site owner.'); }
    const controller = new AbortController();
    const multipart = body instanceof FormData;
    const timeout = setTimeout(() => controller.abort(), multipart || download ? 45000 : 15000);
    try {
      const response = await fetch(base.replace(/\/$/, '') + path, {
        method, signal: controller.signal, headers: body === undefined || multipart ? {} : {'Content-Type': 'application/json'},
        ...(body === undefined ? {} : {body: multipart ? body : JSON.stringify(body)})
      });
      if (response.status === 204) return null;
      if (response.ok && download) return await response.blob();
      let data;
      try { data = await response.json(); } catch { throw new TypeError('Unreadable API response'); }
      if (!response.ok) {
        const error = new Error(response.status === 404 && domain === 'restaurants' ? 'This restaurant was not found. Return to the catalog to choose another.' : data.message || 'This request could not be completed.');
        error.status = response.status;
        error.code = data.error;
        if (uncertain && response.status >= 500) error.message += ' ' + uncertain;
        throw error;
      }
      return data;
    } catch (error) {
      if (error instanceof TypeError || error.name === 'AbortError') {
        throw new Error(method === 'GET'
          ? 'The service is starting up or unavailable. Try loading again in a moment.'
          : method === 'DELETE'
            ? 'Removal could not be confirmed. Use Retry cleanup to finish safely.'
            : 'The result could not be confirmed. ' + (uncertain || 'Check your saved list before trying again.'));
      }
      throw error;
    } finally { clearTimeout(timeout); }
  }

  function showError(node, error) {
    const details = node.closest('details');
    if (details) details.open = true;
    node.textContent = error.message;
    node.hidden = false;
    node.focus();
  }

  async function mutation(button, task, errorNode) {
    if (busy) { notice('Please wait for the current request to finish.'); return; }
    busy = true;
    notice('');
    button.disabled = true;
    try { await task(); } catch (error) { showError(errorNode, error); }
    finally { busy = false; button.disabled = false; }
  }

  function savePending() {
    try { localStorage.setItem('picky-cleanup', JSON.stringify(pending)); } catch { /* Continue in memory. */ }
    renderCleanup();
  }

  function renderCleanup() {
    const section = $('#cleanup');
    section.hidden = !pending.length;
    section.replaceChildren();
    if (!pending.length) return;
    const heading = document.createElement('h2'); heading.textContent = 'Removal needs confirmation'; section.append(heading);
    for (const row of pending) {
      const text = document.createElement('p'); text.textContent = `${row.title}: saved-entry removal or dining cleanup is unconfirmed. Retry the same cleanup to finish.`;
      const button = document.createElement('button'); button.textContent = `Retry cleanup for ${row.title}`;
      const error = document.createElement('p'); error.className = 'message error'; error.hidden = true; error.tabIndex = -1; error.setAttribute('role', 'alert');
      button.addEventListener('click', () => mutation(button, async () => {
        await api('restaurants', `/saved-restaurants/${row.id}`, {method: 'DELETE'});
        pending = pending.filter(item => item.id !== row.id); savePending();
        notice('Removal and dining cleanup confirmed. The restaurant remains in the catalog.');
        await render();
      }, error));
      section.append(text, button, error);
    }
  }

  async function removeRestaurant(row, button, error) {
    if (!confirm(`Remove ${row.title} from your saved list and permanently delete its visits, items and bills? The restaurant will remain in the catalog.`)) return;
    await mutation(button, async () => {
      try {
        await api('restaurants', `/saved-restaurants/${row.saved.id}`, {method: 'DELETE'});
        pending = pending.filter(item => item.id !== row.saved.id); savePending();
        notice('Removed from your saved list; visits and bills deleted. The restaurant remains in the catalog.');
      } catch (failure) {
        if (!pending.some(item => item.id === row.saved.id)) pending.push({id: row.saved.id, title: row.title});
        savePending();
        throw failure;
      }
      await render();
    }, error);
  }

  function saveChoice(row) {
    const wrapper = document.createElement('details'); wrapper.className = 'save-choice';
    wrapper.innerHTML = `<summary>Save restaurant</summary><form><div class="field"><label for="save-${row.id}">Saved status for ${esc(row.title)}</label><select id="save-${row.id}" name="status"><option value="want_to_go">Want to go</option><option value="visited">Visited already</option></select></div><p class="message error" role="alert" tabindex="-1" hidden></p><button type="submit">Add to saved list</button></form>`;
    const form = wrapper.querySelector('form');
    form.addEventListener('submit', event => {
      event.preventDefault();
      mutation(form.querySelector('button'), async () => {
        await api('restaurants', `/restaurants/${row.id}/saved-entry`, {method:'POST', body:{status: new FormData(form).get('status')}});
        notice(`${row.title} added to your saved list.`);
        await render();
      }, form.querySelector('[role=alert]'));
    });
    return wrapper;
  }

  function item(row) {
    const li = document.createElement('li');
    const link = document.createElement('a'); link.className = 'restaurant-card-link'; link.href = `#/restaurants/${row.id}`;
    link.innerHTML = `<strong>${esc(row.title)}</strong><p>${esc([row.category_name || 'Category not set', row.city, row.price === null ? null : `Price ${row.price}/4`, row.saved?.rating == null ? null : `Your rating ${row.saved.rating}/5`].filter(Boolean).join(' · '))}</p>${row.address ? `<p class="restaurant-address">${esc(row.address)}</p>` : ''}`;
    const actions = document.createElement('div'); actions.className = 'catalog-actions';
    const status = document.createElement('span'); status.className = 'status' + (row.saved ? '' : ' unsaved'); status.textContent = statuses[row.saved?.status || 'not_saved']; actions.append(status);
    li.append(link, actions);
    if (row.saved) {
      const button = document.createElement('button'); button.className = 'remove-button'; button.textContent = 'Remove'; button.setAttribute('aria-label', `Remove ${row.title}`);
      const error = document.createElement('p'); error.hidden = true; error.className = 'message error'; error.tabIndex = -1; error.setAttribute('role', 'alert');
      button.addEventListener('click', () => removeRestaurant(row, button, error));
      actions.append(button, error);
    } else { actions.append(saveChoice(row)); }
    return li;
  }

  function filters(params) {
    const details = document.createElement('details'); details.className = 'filter-panel'; details.open = params.size > 0;
    details.innerHTML = '<summary>Filters</summary><form class="filter-form"><div class="field-grid"><div class="field"><label for="filter-category">Cuisine</label><input id="filter-category" name="category" maxlength="200"></div><div class="field"><label for="filter-city">City</label><input id="filter-city" name="city" maxlength="200"></div><div class="field"><label for="filter-price">Price level</label><select id="filter-price" name="price"><option value="">Any price</option><option value="1">1 / 4</option><option value="2">2 / 4</option><option value="3">3 / 4</option><option value="4">4 / 4</option></select></div><div class="field"><label for="filter-rating">Minimum personal rating</label><input id="filter-rating" name="min_rating" type="number" min="0" max="5" step="0.1"></div><div class="field"><label for="filter-status">Saved status</label><select id="filter-status" name="status"><option value="">Any status</option><option value="want_to_go">Want to go</option><option value="visited">Visited</option><option value="not_saved">Not saved</option></select></div></div><div class="form-actions"><button type="submit">Apply filters</button><a class="filter-clear" href="#/catalog">Clear filters</a></div></form>';
    const form = details.querySelector('form');
    for (const input of form.elements) if (input.name) input.value = params.get(input.name) || '';
    form.addEventListener('submit', event => {
      event.preventDefault(); const next = new URLSearchParams();
      for (const [key, value] of new FormData(form)) if (value.trim()) next.set(key, value.trim());
      const target = '#/catalog' + (next.size ? `?${next}` : '');
      if (location.hash === target) render(); else location.hash = target;
    });
    return details;
  }

  async function renderList(catalog, params, token) {
    const rows = await api('restaurants', catalog ? '/restaurants' + (params.size ? `?${params}` : '') : '/saved-restaurants');
    if (token !== generation) return;
    const heading = catalog ? 'All restaurants' : 'Saved restaurants';
    content.innerHTML = `<h2 tabindex="-1">${heading}</h2>`;
    if (catalog) content.append(filters(params));
    const count = document.createElement('p'); count.className = 'list-summary'; count.textContent = `${rows.length} restaurant${rows.length === 1 ? '' : 's'}${params.size ? (rows.length === 1 ? ' matches your filters' : ' match your filters') : catalog ? ' in the catalog' : ' saved'}.`; content.append(count);
    if (!rows.length) {
      const empty = document.createElement('p'); empty.className = 'empty-state'; empty.textContent = params.size ? 'No restaurants match these filters. Change or clear the filters to see more.' : catalog ? 'No restaurants in the catalog yet. Add a restaurant to begin.' : 'Your saved list is empty. Add a restaurant or save one from All restaurants.'; content.append(empty);
    } else {
      const ul = document.createElement('ul'); ul.className = 'restaurant-list'; rows.forEach(row => ul.append(item(row))); content.append(ul);
    }
  }

  function composer(label, fields, action, submit) {
    const details = document.createElement('details'); details.className = 'visit-composer';
    const summary = document.createElement('summary'); summary.textContent = label;
    const form = document.createElement('form');
    form.innerHTML = `<fieldset>${fields}<p class="message error" role="alert" tabindex="-1" hidden></p><div class="form-actions"><button type="submit">${esc(action)}</button><button type="button" class="secondary-button">Cancel</button></div></fieldset>`;
    const fieldset = form.querySelector('fieldset'), error = form.querySelector('[role=alert]');
    form.querySelector('[type=button]').onclick = () => { details.open = false; summary.focus(); };
    form.addEventListener('keydown', event => { if (event.key === 'Escape' && !busy) { details.open = false; summary.focus(); } });
    form.onsubmit = event => {
      event.preventDefault(); const data = new FormData(form); error.hidden = true;
      mutation(form.querySelector('[type=submit]'), async () => {
        fieldset.disabled = true;
        try { await submit(data, form); } finally { fieldset.disabled = false; }
      }, error);
    };
    details.append(summary, form); return details;
  }

  function field(id, name, label, attributes = '', value = '') {
    return `<div class="field"><label for="${id}">${label}</label><input id="${id}" name="${name}" ${attributes} value="${esc(value)}"></div>`;
  }

  const optionalNumber = value => value === '' ? null : Number(value);
  async function refreshDetail(token, message) {
    notice(message);
    if (token === generation) await render();
  }

  function savedEditor(row, token) {
    const saved = row.saved, id = saved.id;
    const form = composer('Edit your details',
      field(`personal-rating-${id}`, 'rating', 'Your overall rating', 'type="number" min="0" max="5" step="0.1"', saved.rating ?? '') +
      `<div class="field"><label for="personal-notes-${id}">Your notes</label><textarea id="personal-notes-${id}" name="notes" maxlength="2000" rows="3">${esc(saved.notes)}</textarea></div><div class="field"><label for="return-${id}">Would you go back?</label><select id="return-${id}" name="would_go_back"><option value="">Not set</option><option value="true">Yes</option><option value="false">No</option></select></div>`,
      'Save your details', async data => {
        await api('restaurants', `/saved-restaurants/${id}`, {method: 'PATCH', body: {
          rating: optionalNumber(data.get('rating')), notes: data.get('notes') || null,
          would_go_back: data.get('would_go_back') === '' ? null : data.get('would_go_back') === 'true'
        }, uncertain: 'Reload this restaurant to check your details before saving again.'});
        await refreshDetail(token, 'Your details saved.');
      });
    form.querySelector('select').value = saved.would_go_back == null ? '' : String(Boolean(saved.would_go_back));
    return form;
  }

  function locationEditor(row, token) {
    const id = row.id;
    const form = composer('Edit location',
      field(`location-address-${id}`, 'address', 'Address (required)', 'required maxlength="300"', row.address ?? '') +
      `<div class="field"><label for="location-mode-${id}">How to find the location</label><select id="location-mode-${id}" name="mode"><option value="search">Look up address</option><option value="manual">Enter coordinates</option></select><small class="field-hint">Address lookup sends this address to OpenStreetMap. If lookup fails, enter coordinates below.</small></div><div class="field-grid" data-coordinates>` +
      field(`latitude-${id}`, 'latitude', 'Latitude (required)', 'type="number" min="-90" max="90" step="any" required', row.latitude ?? '') +
      field(`longitude-${id}`, 'longitude', 'Longitude (required)', 'type="number" min="-180" max="180" step="any" required', row.longitude ?? '') + '</div>',
      'Save location', async data => {
        const body = {mode: data.get('mode'), address: data.get('address')};
        if (body.mode === 'manual') Object.assign(body, {latitude: Number(data.get('latitude')), longitude: Number(data.get('longitude'))});
        try {
          await api('restaurants', `/restaurants/${id}/location`, {method: 'PUT', body,
            uncertain: 'Reload this restaurant to check its location before saving again.'});
        } catch (error) {
          if (body.mode === 'search' && error.status === 400) error.message = 'Address lookup could not find this location or is unavailable. Check the address or select Enter coordinates.';
          throw error;
        }
        await refreshDetail(token, 'Location saved.');
      });
    const mode = form.querySelector('select'), coordinates = form.querySelector('[data-coordinates]');
    mode.value = row.latitude == null || row.longitude == null ? 'search' : 'manual';
    const toggle = () => { coordinates.hidden = mode.value !== 'manual'; coordinates.querySelectorAll('input').forEach(input => { input.disabled = coordinates.hidden; }); };
    mode.onchange = toggle; toggle(); return form;
  }

  function visitComposer(savedId, token) {
    const parts = new Intl.DateTimeFormat('en', {timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit'}).formatToParts(new Date());
    const date = ['year', 'month', 'day'].map(key => parts.find(part => part.type === key).value).join('-');
    return composer('Record a visit',
      field(`visit-date-${savedId}`, 'visit_date', 'Visit date (required)', `type="date" required max="${date}"`, date) + '<p class="field-hint">Dates use Madrid time.</p>' +
      field(`visit-rating-${savedId}`, 'rating', 'Visit rating', 'type="number" min="0" max="5" step="0.1"') +
      `<div class="field"><label for="visit-notes-${savedId}">Visit notes</label><textarea id="visit-notes-${savedId}" name="notes" maxlength="2000" rows="3"></textarea></div><p class="field-hint">Recording a visit also marks this restaurant as visited.</p>`,
      'Save visit', async data => {
        await api('dining', `/saved-restaurants/${savedId}/visits`, {method: 'POST', body: {
          visit_date: data.get('visit_date'), rating: optionalNumber(data.get('rating')), notes: data.get('notes') || null
        }, uncertain: 'Reload visit history before trying again to avoid a duplicate visit.'});
        await refreshDetail(token, 'Visit saved and restaurant marked visited.');
      });
  }

  function visitEntry(visit, savedId, token) {
    const li = document.createElement('li');
    const heading = document.createElement('h4'); heading.textContent = `${visit.visit_date}${visit.rating == null ? '' : ` · Rating ${visit.rating}/5`}`; li.append(heading);
    if (visit.notes) { const notes = document.createElement('p'); notes.className = 'visit-notes'; notes.textContent = visit.notes; li.append(notes); }
    const path = `/saved-restaurants/${savedId}/visits/${visit.id}`;
    const items = document.createElement('ul'); items.className = 'item-list';
    for (const item of visit.items) {
      const price = item.unit_price == null ? '' : ` · Unit price ${item.unit_price.toFixed(2)}`;
      const total = item.line_total == null ? '' : ` · Total ${item.line_total.toFixed(2)}`;
      const entry = document.createElement('li');
      entry.textContent = `${item.item_name} × ${item.quantity}${price}${total}`;
      items.append(entry);
    }
    if (visit.items.length) li.append(items);
    li.append(composer('Add an ordered item',
      field(`item-name-${visit.id}`, 'item_name', 'Item name (required)', 'required maxlength="300"') +
      '<div class="field-grid">' + field(`quantity-${visit.id}`, 'quantity', 'Quantity (required)', 'type="number" min="1" max="2147483647" step="1" required', 1) +
      field(`unit-price-${visit.id}`, 'unit_price', 'Unit price', 'type="number" min="0" max="9999999999.99" step="0.01"') + '</div>',
      'Save item', async data => {
        await api('dining', path + '/items', {method: 'POST', body: {
          item_name: data.get('item_name'), quantity: Number(data.get('quantity')), unit_price: optionalNumber(data.get('unit_price'))
        }, uncertain: 'Reload visit history to check its items before trying again.'});
        await refreshDetail(token, 'Ordered item saved.');
      }));
    const billList = document.createElement('ul'); billList.className = 'bill-list';
    for (const bill of visit.bills) {
      const entry = document.createElement('li'), button = document.createElement('button'), error = document.createElement('p');
      button.type = 'button'; button.className = 'secondary-button'; button.textContent = `Download bill ${bill.id}`;
      error.className = 'message error'; error.hidden = true; error.tabIndex = -1; error.setAttribute('role', 'alert');
      button.onclick = () => mutation(button, async () => {
        error.hidden = true;
        const blob = await api('dining', path + '/bills/' + bill.id, {download: true});
        const extension = {'application/pdf': 'pdf', 'image/png': 'png', 'image/jpeg': 'jpg'}[blob.type];
        if (!extension || blob.size > 5242880) throw new Error('This bill could not be downloaded. Reload visit history and try again.');
        const url = URL.createObjectURL(blob), link = document.createElement('a'); link.href = url; link.download = `bill-${bill.id}.${extension}`;
        document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
        notice('Bill download started.');
      }, error);
      entry.append(button, error); billList.append(entry);
    }
    if (visit.bills.length) li.append(billList);
    li.append(composer('Upload a bill',
      field(`bill-file-${visit.id}`, 'bill_file', 'Bill file (required)', 'type="file" accept="image/png,image/jpeg,application/pdf" required') +
      '<p class="field-hint">PNG, JPEG or PDF, up to 5 MiB. Your file is stored with this visit.</p>', 'Upload bill', async data => {
        const file = data.get('bill_file');
        if (!file.size || file.size > 5242880) throw new Error('Choose a nonempty PNG, JPEG or PDF of at most 5 MiB.');
        try {
          await api('dining', path + '/bills', {method: 'POST', body: data,
            uncertain: 'Reload visit history to check its bills before uploading again.'});
        } catch (error) {
          if (error.status === 400) error.message = 'This file was not accepted. Choose a valid PNG, JPEG or PDF bill.';
          throw error;
        }
        await refreshDetail(token, 'Bill uploaded.');
      }));
    return li;
  }

  async function renderDetail(id, token) {
    const row = await api('restaurants', `/restaurants/${id}`);
    if (token !== generation) return;
    document.title = `${row.title} · Picky`;
    content.innerHTML = `<p class="back-link"><a href="${esc(lastList)}">Back to restaurants</a></p><div class="detail-heading"><h2 tabindex="-1">${esc(row.title)}</h2><span class="status">${esc(statuses[row.saved?.status || 'not_saved'])}</span></div>`;
    if (row.description) { const p = document.createElement('p'); p.className = 'detail-description'; p.textContent = row.description; content.append(p); }
    const facts = [['Cuisine', row.category_name], ['City', row.city], ['Price', row.price == null ? null : `${row.price}/4`], ['General score', row.total_score == null ? null : `${row.total_score}/5`], ['Your rating', row.saved?.rating == null ? null : `${row.saved.rating}/5`], ['Would go back', row.saved?.would_go_back == null ? null : row.saved.would_go_back ? 'Yes' : 'No'], ['Phone', row.phone], ['Address', row.address], ['Postal code', row.postal_code], ['Region', row.state], ['Country', row.country_code], ['Review count', row.reviews_count]];
    const dl = document.createElement('dl'); dl.className = 'detail-grid';
    for (const [label, value] of facts) {
      const div = document.createElement('div'); const dt = document.createElement('dt'); dt.textContent = label; const dd = document.createElement('dd'); dd.textContent = value ?? 'Not set'; div.append(dt, dd); dl.append(div);
    }
    content.append(dl);
    if (row.website) {
      try { const url = new URL(row.website); if (['https:', 'http:'].includes(url.protocol)) { const link = document.createElement('a'); link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Restaurant website'; content.append(link); } } catch { /* Do not turn invalid URLs into active links. */ }
    }
    if (row.menu) { const p = document.createElement('p'); p.className = 'detail-section'; p.textContent = `Menu: ${row.menu}`; content.append(p); }
    if (row.saved?.notes) { const p = document.createElement('p'); p.className = 'detail-section personal-notes'; p.textContent = row.saved.notes; content.append(p); }
    content.append(locationEditor(row, token));
    if (row.latitude != null && row.longitude != null) {
      const map = document.createElement('a'); map.href = `https://www.openstreetmap.org/?mlat=${encodeURIComponent(row.latitude)}&mlon=${encodeURIComponent(row.longitude)}#map=16/${encodeURIComponent(row.latitude)}/${encodeURIComponent(row.longitude)}`;
      map.target = '_blank'; map.rel = 'noopener noreferrer'; map.textContent = `View location on OpenStreetMap (${row.latitude}, ${row.longitude})`; content.append(map);
    }
    if (!row.saved) { content.append(saveChoice(row)); return; }
    content.append(savedEditor(row, token));
    const history = document.createElement('section'); history.className = 'detail-section'; history.innerHTML = '<h3>Visit history</h3><p>Loading visits…</p>'; history.setAttribute('aria-busy', 'true'); content.append(history);
    api('dining', `/saved-restaurants/${row.saved.id}/visits`).then(visits => {
      if (token !== generation) return;
      history.innerHTML = '<h3>Visit history</h3>';
      const refresh = document.createElement('button'); refresh.type = 'button'; refresh.className = 'secondary-button'; refresh.textContent = 'Refresh visit history'; refresh.onclick = () => render(); history.append(refresh);
      history.append(visitComposer(row.saved.id, token));
      if (!visits.length) { const p = document.createElement('p'); p.textContent = 'No visits recorded yet.'; history.append(p); }
      const list = document.createElement('ul'); list.className = 'visit-list';
      for (const visit of visits) list.append(visitEntry(visit, row.saved.id, token));
      history.append(list);
    }).catch(() => {
      if (token !== generation) return;
      history.innerHTML = '<h3>Visit history</h3><p class="message error" role="alert">Dining history is starting up or unavailable. Restaurant details are still available.</p>';
      const retry = document.createElement('button'); retry.textContent = 'Retry visit history'; retry.onclick = () => render(); history.append(retry);
    }).finally(() => history.removeAttribute('aria-busy'));
  }

  async function render(focus = true) {
    const token = ++generation;
    const route = location.hash.slice(1) || '/saved';
    const [path, search = ''] = route.split('?');
    $('#saved-nav').removeAttribute('aria-current'); $('#catalog-nav').removeAttribute('aria-current');
    if (path === '/saved' || path === '/catalog') {
      lastList = location.hash || '#/saved';
      $(path === '/saved' ? '#saved-nav' : '#catalog-nav').setAttribute('aria-current', 'page');
    }
    document.title = path === '/catalog' ? 'Picky · All restaurants' : 'Picky · Saved restaurants';
    content.setAttribute('aria-busy', 'true'); content.innerHTML = '<h2 tabindex="-1">Loading restaurants…</h2>';
    try {
      if (path === '/saved' || path === '/catalog') await renderList(path === '/catalog', new URLSearchParams(search), token);
      else if (/^\/restaurants\/[1-9]\d*$/.test(path)) await renderDetail(path.split('/')[2], token);
      else throw new Error('Page not found. Use Saved restaurants or All restaurants to continue.');
    } catch (error) {
      if (token !== generation) return;
      content.innerHTML = '<h2 tabindex="-1">Could not load restaurants</h2><p class="message error" role="alert"></p><button type="button">Try loading again</button>';
      content.querySelector('[role=alert]').textContent = error.message;
      if (error.status === 404) {
        content.querySelector('h2').textContent = 'Restaurant not found';
        content.querySelector('button').textContent = 'Browse all restaurants';
        content.querySelector('button').onclick = () => { location.hash = '#/catalog'; };
      } else { content.querySelector('button').onclick = () => render(); }
    } finally {
      if (token === generation) { content.removeAttribute('aria-busy'); if (focus) content.querySelector('h2')?.focus(); }
    }
  }

  function closeAdd() {
    $('#add-panel').hidden = true; $('#add-toggle').setAttribute('aria-expanded', 'false'); $('#add-toggle').setAttribute('aria-label', 'Add a restaurant'); $('#add-toggle').textContent = '+'; $('#add-toggle').focus();
  }
  $('#add-toggle').onclick = () => {
    const open = $('#add-panel').hidden; $('#add-panel').hidden = !open; $('#add-toggle').setAttribute('aria-expanded', String(open));
    $('#add-toggle').textContent = open ? '×' : '+'; $('#add-toggle').setAttribute('aria-label', open ? 'Close add restaurant form' : 'Add a restaurant');
    if (open) $('#title').focus();
  };
  $('#cancel-add').onclick = closeAdd;
  $('#add-panel').addEventListener('keydown', event => { if (event.key === 'Escape') closeAdd(); });
  $('#add-form').onsubmit = event => {
    event.preventDefault(); const form = event.currentTarget; const data = Object.fromEntries(new FormData(form));
    for (const key of ['price', 'rating']) data[key] = data[key] === '' ? null : Number(data[key]);
    for (const key of ['category_name', 'city', 'address', 'notes']) if (data[key] === '') data[key] = null;
    $('#add-error').hidden = true;
    mutation(form.querySelector('[type=submit]'), async () => {
      await api('restaurants', '/restaurants', {method:'POST', body:data});
      form.reset(); closeAdd(); notice('Restaurant saved successfully.');
      if (location.hash !== '#/saved') location.hash = '#/saved'; else await render();
    }, $('#add-error'));
  };
  $('.skip-link').addEventListener('click', event => { event.preventDefault(); content.focus(); });
  window.addEventListener('hashchange', () => { $('#add-panel').hidden = true; $('#add-toggle').setAttribute('aria-expanded', 'false'); $('#add-toggle').setAttribute('aria-label', 'Add a restaurant'); $('#add-toggle').textContent = '+'; render(true); });
  renderCleanup(); render(false);
})();
