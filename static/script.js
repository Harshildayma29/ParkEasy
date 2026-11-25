// ParkEasy student project JavaScript.
// Fetch data from Python, show parking cards, and display saved bookings.
let parkingList = [];
let currentUser = null;
const byId = (id) => document.getElementById(id);

async function getData(url, options = {}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong');
  return data;
}

function showParking() {
  const query = byId('search').value.trim().toLowerCase();
  const vehicle = byId('vehicle').value;
  const selectedArea = byId('areaFilter').value;
  const suffix = vehicle === '2W' ? '2w' : '4w';
  const availableOnly = byId('availability').value === 'available';
  const matches = parkingList.filter(p =>
    (p.name + ' ' + p.area).toLowerCase().includes(query) &&
    (selectedArea === 'all' || p.area === selectedArea) &&
    (!availableOnly || p['available_' + suffix] > 0)
  );
  byId('summary').textContent = `${matches.length} parking locations found for ${vehicle === '2W' ? 'bikes' : 'cars'}`;
  byId('parkingCards').replaceChildren();
  matches.forEach(p => {
    const free = p['available_' + suffix];
    const total = p['total_' + suffix];
    const price = p['price_' + suffix];
    const percent = p['chance_' + suffix];
    const card = document.createElement('article');
    card.className = 'parking-card';
    card.innerHTML = `<div class="card-top"><span class="parking-icon">🅿️</span><span class="pill"></span></div>
      <h3></h3><p class="area"></p>
      <div class="info-row"><span>Free spaces</span><strong class="spaces"></strong></div>
      <div class="info-row"><span>Spaces available</span><strong class="percent"></strong></div>
      <div class="card-bottom"><div><span class="price"></span><span class="muted"> / hour</span></div><button class="button book-btn"></button></div>`;
    card.querySelector('h3').textContent = p.name;
    card.querySelector('.area').textContent = p.area + ', Ahmedabad';
    card.querySelector('.spaces').textContent = `${free} / ${total}`;
    card.querySelector('.percent').textContent = `${Number(percent).toFixed(2)}%`;
    card.querySelector('.price').textContent = `₹${price}`;
    card.querySelector('.pill').textContent = free > 0 ? 'Available' : 'Full';
    if (!free) card.querySelector('.pill').classList.add('full');
    const button = card.querySelector('.book-btn');
    button.textContent = free > 0 ? 'Book Now' : 'Full';
    button.disabled = free === 0;
    button.addEventListener('click', () => {
      const url = `/payment?parking_id=${p.id}&vehicle=${vehicle}`;
      if (!currentUser) { location.href = '/login?next=' + encodeURIComponent(url); return; }
      location.href = url;
    });
    byId('parkingCards').append(card);
  });
  const totalFree = parkingList.reduce((sum,p) => sum + p['available_' + suffix], 0);
  const totalSpaces = parkingList.reduce((sum,p) => sum + p['total_' + suffix], 0);
  const percentage = totalSpaces ? (totalFree * 100 / totalSpaces).toFixed(2) : "0.00";
  byId('estimateExample').textContent = `${totalFree} free ÷ ${totalSpaces} total × 100 = ${percentage}%`;
  byId('statFree').textContent = totalFree.toLocaleString('en-IN');
  byId('statTotal').textContent = totalSpaces.toLocaleString('en-IN');
  byId('statPercent').textContent = `${percentage}%`;
  drawProbabilityGraph(matches, suffix, vehicle);
}


// Visual probability-style chart: availability ratio is used as a simple estimate.
// This is NOT a statistically trained probability model.
function drawProbabilityGraph(matches, suffix, vehicle) {
  const graph = byId('probabilityGraph');
  graph.replaceChildren();
  byId('graphVehicle').textContent = vehicle === '2W' ? '2-Wheeler (Bike)' : '4-Wheeler (Car)';
  const sorted = [...matches].sort((a,b) => b['chance_' + suffix] - a['chance_' + suffix]).slice(0, 10);
  byId('graphNote').textContent = `Showing ${sorted.length} of ${matches.length} matching locations · Sample availability, not a future prediction.`;
  if (!sorted.length) { graph.textContent = 'No parking locations match your filters.'; return; }
  for (const place of sorted) {
    const pct = Math.max(0, Math.min(100, place['chance_' + suffix]));
    const line = document.createElement('div'); line.className = 'graph-row';
    const name = document.createElement('span'); name.className = 'graph-name'; name.textContent = place.name; name.title = place.name;
    const track = document.createElement('div'); track.className = 'graph-track';
    const bar = document.createElement('div'); bar.className = 'graph-bar';
    bar.style.width = pct.toFixed(2) + '%'; bar.title = pct + '% spaces available';
    track.append(bar); track.setAttribute('role','progressbar'); track.setAttribute('aria-valuenow', String(pct)); track.setAttribute('aria-valuemin','0'); track.setAttribute('aria-valuemax','100'); track.setAttribute('aria-label', place.name + ' percent available');
    const value = document.createElement('strong'); value.className = 'graph-value'; value.textContent = pct.toFixed(2) + '%';
    line.append(name, track, value); graph.append(line);
  }
}

async function loadBookings() {
  if (!currentUser) return;
  const area = byId('bookingArea');
  const rows = await getData('/api/bookings');
  area.replaceChildren();
  if (!rows.length) { area.textContent = 'No bookings yet. Choose a location above to make one.'; return; }
  rows.forEach(item => {
    const box = document.createElement('div'); box.className = 'booking-item';
    const details = document.createElement('div');
    const title = document.createElement('strong'); title.textContent = `Booking #${item.id} – ${item.name}`;
    const info = document.createElement('p');
    info.textContent = `${item.vehicle_type === '2W' ? 'Bike' : 'Car'} · ${item.number_plate || 'No plate (older booking)'} · ${item.hours} hr · ₹${item.amount} · ${item.status} · ${item.booked_at}`;
    const payment = document.createElement('span'); payment.className = 'payment-label';
    payment.textContent = item.payment_status === 'paid_demo' ? `✓ Demo paid · ${item.payment_method}` : item.payment_method === 'Cash at parking' ? '₹ Pay on arrival' : 'Payment not recorded';
    details.append(title,info,payment); box.append(details);
    if (item.status === 'booked') {
      const cancel = document.createElement('button'); cancel.className = 'button outline small';
      cancel.textContent = 'Cancel Booking';
      cancel.addEventListener('click', async () => {
        if (!confirm('Cancel this booking?')) return;
        try {
          await getData(`/api/bookings/${item.id}/cancel`, {method:'POST'});
          parkingList = await getData('/api/parking');
          showParking(); await loadBookings();
        } catch (e) { alert(e.message); }
      });
      box.append(cancel);
    }
    area.append(box);
  });
}

async function start() {
  try {
    const [spots, account] = await Promise.all([getData('/api/parking'),getData('/api/me')]);
    parkingList = spots; currentUser = account.user;
    // Build the dropdown from the areas stored in the database.
    const areaSelect = byId('areaFilter');
    [...new Set(parkingList.map(p => p.area))].sort((a,b) => a.localeCompare(b)).forEach(area => {
      const option = document.createElement('option');
      option.value = area;
      option.textContent = area;
      areaSelect.append(option);
    });
    if (currentUser) {
      byId('accountLinks').replaceChildren();
      const name = document.createElement('span'); name.textContent = 'Hi, ' + currentUser.name + '  ';
      const logout = document.createElement('button'); logout.className = 'button outline small'; logout.textContent = 'Logout';
      logout.addEventListener('click', async () => {await getData('/api/logout', {method:'POST'}); location.reload();});
      byId('accountLinks').append(name,logout);
      await loadBookings();
    }
    showParking();
  } catch (error) { byId('summary').textContent = 'Cannot reach the server: ' + error.message; }
  ['search','areaFilter','vehicle','availability'].forEach(id => byId(id).addEventListener('input', showParking));
  byId('clearFilters').addEventListener('click', () => {
    byId('search').value = ''; byId('areaFilter').value = 'all'; byId('vehicle').value = '2W'; byId('availability').value = 'all'; showParking();
  });
}
document.addEventListener('DOMContentLoaded', start);
