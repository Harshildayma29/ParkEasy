// ParkEasy checkout simulation: never requests real financial credentials.
let selectedParking;
let vehicle;
const $ = (id) => document.getElementById(id);
const form = $('paymentForm');
const info = $('selectionInfo');
const resultBox = $('message');
const rupees = (n) => '₹' + Number(n).toLocaleString('en-IN');
function selectedMethod() { return document.querySelector('input[name="method"]:checked').value; }
function updateAmount() {
  if (!selectedParking) return;
  const suffix = vehicle === '2W' ? '2w' : '4w';
  const hours = Number($('hours').value);
  const amount = hours * selectedParking['price_' + suffix];
  $('totalAmount').textContent = rupees(amount);
  $('orderDuration').textContent = hours + (hours === 1 ? ' hour' : ' hours');
  $('confirmButton').textContent = (selectedMethod() === 'Cash at parking' ? 'Confirm booking · Pay on arrival ' : 'Confirm demo payment · ') + rupees(amount);
  document.querySelectorAll('.method-card').forEach(el => el.classList.toggle('selected', el.querySelector('input').checked));
  const m = selectedMethod();
  $('paymentPreview').textContent = m === 'Cash at parking'
    ? 'Pay on arrival: your payment status will be Pending (cash), not paid.'
    : `${m === 'Demo UPI' ? 'UPI' : 'Card'} simulation: your reservation will be marked Demo paid. No real money is transferred.`;
}
async function load() {
  const params = new URLSearchParams(location.search);
  vehicle = params.get('vehicle');
  const id = Number(params.get('parking_id'));
  if (!['2W','4W'].includes(vehicle) || !Number.isInteger(id) || id < 1) {
    info.textContent = 'Invalid parking selection.'; form.hidden = true; return;
  }
  const [pRes, aRes] = await Promise.all([fetch('/api/parking'), fetch('/api/me')]);
  if (!pRes.ok || !aRes.ok) throw new Error('Cannot load parking details.');
  const places = await pRes.json(); const account = await aRes.json();
  if (!account.user) { location.href = '/login?next=' + encodeURIComponent(location.pathname + location.search); return; }
  selectedParking = places.find(p => p.id === id);
  if (!selectedParking) { info.textContent = 'Parking location not found.'; form.hidden = true; return; }
  const suffix = vehicle === '2W' ? '2w' : '4w';
  if (selectedParking['available_' + suffix] < 1) { info.textContent = 'This parking location is full. Please choose another.'; form.hidden = true; return; }
  info.textContent = `${selectedParking.name} · ${selectedParking.area}, Ahmedabad`;
  $('orderPlace').textContent = selectedParking.name;
  $('orderArea').textContent = selectedParking.area + ', Ahmedabad';
  $('orderVehicle').textContent = vehicle === '2W' ? '2-Wheeler (Bike)' : '4-Wheeler (Car)';
  $('orderRate').textContent = rupees(selectedParking['price_' + suffix]) + ' / hour';
  $('orderSpaces').textContent = selectedParking['available_' + suffix] + ' free';
  updateAmount();
}
function addReceiptRow(parent, label, value) {
  const row = document.createElement('div'); row.className = 'receipt-row';
  const key = document.createElement('span'); key.textContent = label;
  const data = document.createElement('strong'); data.textContent = value;
  row.append(key, data); parent.append(row);
}
form.addEventListener('submit', async event => {
  event.preventDefault(); if (!selectedParking) return;
  const button = $('confirmButton'); button.disabled = true; button.textContent = 'Saving reservation…';
  const method = selectedMethod();
  try {
    const response = await fetch('/api/book', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({
      parking_id:selectedParking.id, vehicle_type:vehicle, hours:Number($('hours').value),
      payment_method:method, number_plate:$('numberPlate').value.trim().toUpperCase()
    })});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Booking could not be saved.');
    form.hidden = true; info.hidden = true; resultBox.className = 'receipt'; resultBox.replaceChildren();
    const check = document.createElement('div');check.className='receipt-check';check.textContent='✓';resultBox.append(check);
    const title = document.createElement('h2');title.textContent='Booking confirmed!';resultBox.append(title);
    const subtitle = document.createElement('p');subtitle.className='muted';subtitle.textContent='Your parking space is reserved in this project simulation.';resultBox.append(subtitle);
    addReceiptRow(resultBox,'Booking ID','#' + data.booking_id);
    addReceiptRow(resultBox,'Parking location',selectedParking.name);
    addReceiptRow(resultBox,'Number plate',data.number_plate);
    addReceiptRow(resultBox,'Duration',$('hours').value + ' hour(s)');
    addReceiptRow(resultBox,'Payment method',method);
    addReceiptRow(resultBox,'Payment status',data.payment_status === 'paid_demo' ? 'Demo paid (simulated)' : 'Pay on arrival');
    if(data.transaction_ref) addReceiptRow(resultBox,'Demo transaction ref',data.transaction_ref);
    addReceiptRow(resultBox,'Total',rupees(data.amount));
    const actions = document.createElement('div');actions.className='receipt-actions';
    const print = document.createElement('button');print.className='button';print.type='button';print.textContent='Print receipt';print.onclick=()=>window.print();
    const back=document.createElement('a');back.className='button outline';back.href='/#bookings';back.textContent='View my bookings';
    actions.append(print,back);resultBox.append(actions);
    resultBox.scrollIntoView({behavior:'smooth',block:'start'});
  } catch(error) {resultBox.className='error checkout-error';resultBox.textContent=error.message;button.disabled=false;updateAmount();}
});
$('hours').addEventListener('change',updateAmount);
document.querySelectorAll('input[name="method"]').forEach(el=>el.addEventListener('change',updateAmount));
load().catch(e=>{info.textContent='Server problem: '+e.message;form.hidden=true;});
