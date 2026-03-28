/* ── CONFIG ──────────────────────────────────────────────── */
const API_BASE = window.ENV_API_URL || 'http://localhost:8000';

/* ── STATE ───────────────────────────────────────────────── */
let products   = [];
let cart       = JSON.parse(localStorage.getItem('eks_cart') || '[]');
let cartOpen   = false;

/* ── DOM REFS ────────────────────────────────────────────── */
const productGrid  = document.getElementById('productGrid');
const emptyState   = document.getElementById('emptyState');
const cartDrawer   = document.getElementById('cartDrawer');
const cartOverlay  = document.getElementById('cartOverlay');
const cartItems    = document.getElementById('cartItems');
const cartEmpty    = document.getElementById('cartEmpty');
const cartFooter   = document.getElementById('cartFooter');
const cartCount    = document.getElementById('cartCount');
const cartSubtotal = document.getElementById('cartSubtotal');
const cartTotal    = document.getElementById('cartTotal');
const searchInput  = document.getElementById('searchInput');
const sortSelect   = document.getElementById('sortSelect');
const toast        = document.getElementById('toast');
const modalOverlay = document.getElementById('modalOverlay');
const modalBody    = document.getElementById('modalBody');

/* ── INIT ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  fetchProducts();
  renderCart();
  bindEvents();
});

/* ── API ─────────────────────────────────────────────────── */
async function fetchProducts() {
  try {
    const res = await fetch(`${API_BASE}/products`);
    if (!res.ok) throw new Error('Failed to fetch');
    products = await res.json();
    renderProducts(products);
  } catch (err) {
    console.error(err);
    // Fallback demo data when backend is unavailable
    products = getDemoProducts();
    renderProducts(products);
    showToast('Using demo data — backend offline');
  }
}

async function apiAddToCart(productId, quantity = 1) {
  try {
    await fetch(`${API_BASE}/cart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity })
    });
  } catch (_) { /* graceful — local cart still updated */ }
}

async function apiRemoveFromCart(cartItemId) {
  try {
    await fetch(`${API_BASE}/cart/${cartItemId}`, { method: 'DELETE' });
  } catch (_) {}
}

async function apiClearCart() {
  try {
    await fetch(`${API_BASE}/cart`, { method: 'DELETE' });
  } catch (_) {}
}

/* ── PRODUCTS ────────────────────────────────────────────── */
function getFilteredProducts() {
  const query = searchInput.value.toLowerCase().trim();
  const sort  = sortSelect.value;

  let list = products.filter(p =>
    p.name.toLowerCase().includes(query) ||
    (p.description || '').toLowerCase().includes(query) ||
    (p.category || '').toLowerCase().includes(query)
  );

  if (sort === 'price-asc')  list = list.sort((a,b) => a.price - b.price);
  if (sort === 'price-desc') list = list.sort((a,b) => b.price - a.price);
  if (sort === 'name-asc')   list = list.sort((a,b) => a.name.localeCompare(b.name));

  return list;
}

function renderProducts(list) {
  productGrid.innerHTML = '';

  if (!list.length) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  list.forEach((p, i) => {
    const card = createProductCard(p, i);
    productGrid.appendChild(card);
  });
}

function createProductCard(p, index) {
  const card = document.createElement('div');
  card.className = 'product-card';
  card.style.animationDelay = `${index * 60}ms`;
  card.innerHTML = `
    <div class="card-image">
      ${p.stock === 0 ? '<span class="card-badge">Out of stock</span>' : ''}
      <span>${p.emoji || '📦'}</span>
    </div>
    <div class="card-body">
      ${p.category ? `<p class="card-category">${escHtml(p.category)}</p>` : ''}
      <h3 class="card-name">${escHtml(p.name)}</h3>
      <p class="card-description">${escHtml(p.description || '')}</p>
    </div>
    <div class="card-footer">
      <p class="card-price">$${Number(p.price).toFixed(2)}</p>
      <button class="btn-add" data-id="${p.id}" ${p.stock === 0 ? 'disabled' : ''}>
        ${p.stock === 0 ? 'Sold out' : 'Add to cart'}
      </button>
    </div>
  `;

  // Click card body → open modal
  card.querySelector('.card-body').addEventListener('click', () => openModal(p));
  card.querySelector('.card-image').addEventListener('click', () => openModal(p));

  // Add to cart button
  card.querySelector('.btn-add').addEventListener('click', e => {
    e.stopPropagation();
    addToCart(p);
  });

  return card;
}

/* ── MODAL ───────────────────────────────────────────────── */
function openModal(p) {
  modalBody.innerHTML = `
    <div class="modal-emoji">${p.emoji || '📦'}</div>
    <p class="modal-category">${escHtml(p.category || 'Product')}</p>
    <h2 class="modal-name">${escHtml(p.name)}</h2>
    <p class="modal-desc">${escHtml(p.description || 'No description available.')}</p>
    <p class="modal-price">$${Number(p.price).toFixed(2)}</p>
    <div class="modal-actions">
      <button class="btn-primary" id="modalAddBtn" ${p.stock === 0 ? 'disabled' : ''}>
        ${p.stock === 0 ? 'Out of stock' : 'Add to cart'}
      </button>
      <button class="btn-outline" onclick="closeModal()">Close</button>
    </div>
  `;
  document.getElementById('modalAddBtn').addEventListener('click', () => {
    addToCart(p);
    closeModal();
  });
  modalOverlay.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modalOverlay.classList.add('hidden');
  document.body.style.overflow = '';
}

/* ── CART: LOCAL ─────────────────────────────────────────── */
function addToCart(product) {
  const existing = cart.find(i => i.product_id === product.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({
      product_id: product.id,
      name:       product.name,
      price:      product.price,
      emoji:      product.emoji || '📦',
      quantity:   1
    });
  }
  persistCart();
  renderCart();
  apiAddToCart(product.id, 1);
  showToast(`${product.name} added to cart`);
  bumpCartBtn();
}

function removeFromCart(productId) {
  const item = cart.find(i => i.product_id === productId);
  cart = cart.filter(i => i.product_id !== productId);
  persistCart();
  renderCart();
  if (item?.cart_item_id) apiRemoveFromCart(item.cart_item_id);
}

function changeQty(productId, delta) {
  const item = cart.find(i => i.product_id === productId);
  if (!item) return;
  item.quantity += delta;
  if (item.quantity <= 0) {
    removeFromCart(productId);
    return;
  }
  persistCart();
  renderCart();
}

function clearCart() {
  cart = [];
  persistCart();
  renderCart();
  apiClearCart();
  showToast('Cart cleared');
}

function persistCart() {
  localStorage.setItem('eks_cart', JSON.stringify(cart));
}

function cartTotal_() {
  return cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
}

function cartItemCount() {
  return cart.reduce((sum, i) => sum + i.quantity, 0);
}

/* ── CART: RENDER ────────────────────────────────────────── */
function renderCart() {
  // Count badge
  const count = cartItemCount();
  cartCount.textContent = count;
  cartCount.classList.toggle('visible', count > 0);

  // Empty vs items
  if (!cart.length) {
    cartEmpty.style.display = 'flex';
    cartFooter.style.display = 'none';
    // Remove old item rows
    cartItems.querySelectorAll('.cart-item').forEach(el => el.remove());
    return;
  }

  cartEmpty.style.display = 'none';
  cartFooter.style.display = 'flex';

  // Rebuild item rows
  cartItems.querySelectorAll('.cart-item').forEach(el => el.remove());

  cart.forEach(item => {
    const row = document.createElement('div');
    row.className = 'cart-item';
    row.dataset.pid = item.product_id;
    row.innerHTML = `
      <div class="cart-item-icon">${item.emoji}</div>
      <div class="cart-item-info">
        <p class="cart-item-name">${escHtml(item.name)}</p>
        <p class="cart-item-price">$${(item.price * item.quantity).toFixed(2)}</p>
      </div>
      <div class="cart-item-qty">
        <button class="qty-btn" data-action="dec" data-pid="${item.product_id}">−</button>
        <span class="qty-num">${item.quantity}</span>
        <button class="qty-btn" data-action="inc" data-pid="${item.product_id}">+</button>
      </div>
      <button class="cart-item-remove" data-pid="${item.product_id}" aria-label="Remove">✕</button>
    `;
    cartItems.appendChild(row);
  });

  // Totals
  const total = cartTotal_();
  cartSubtotal.textContent = `$${total.toFixed(2)}`;
  cartTotal.textContent    = `$${total.toFixed(2)}`;
}

/* ── CART DRAWER OPEN/CLOSE ──────────────────────────────── */
function openCart() {
  cartOpen = true;
  cartDrawer.classList.add('open');
  cartOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeCart() {
  cartOpen = false;
  cartDrawer.classList.remove('open');
  cartOverlay.classList.remove('active');
  document.body.style.overflow = '';
}

/* ── EVENTS ──────────────────────────────────────────────── */
function bindEvents() {
  document.getElementById('cartToggle').addEventListener('click', () =>
    cartOpen ? closeCart() : openCart()
  );
  document.getElementById('cartClose').addEventListener('click', closeCart);
  cartOverlay.addEventListener('click', closeCart);
  document.getElementById('clearCartBtn').addEventListener('click', clearCart);
  document.getElementById('checkoutBtn').addEventListener('click', () =>
    showToast('Checkout coming soon!')
  );
  document.getElementById('modalClose').addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', e => {
    if (e.target === modalOverlay) closeModal();
  });

  // Search + sort
  searchInput.addEventListener('input',  () => renderProducts(getFilteredProducts()));
  sortSelect.addEventListener('change',  () => renderProducts(getFilteredProducts()));

  // Cart item events (delegated)
  cartItems.addEventListener('click', e => {
    const pid    = e.target.dataset.pid || e.target.closest('[data-pid]')?.dataset.pid;
    const action = e.target.dataset.action;
    if (!pid) return;
    if (e.target.classList.contains('cart-item-remove')) removeFromCart(Number(pid));
    else if (action === 'inc') changeQty(Number(pid),  1);
    else if (action === 'dec') changeQty(Number(pid), -1);
  });

  // Keyboard ESC closes
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeCart();
      closeModal();
    }
  });
}

/* ── TOAST ───────────────────────────────────────────────── */
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
}

/* ── CART BTN BUMP ───────────────────────────────────────── */
function bumpCartBtn() {
  const btn = document.getElementById('cartToggle');
  btn.style.transform = 'scale(1.18)';
  setTimeout(() => btn.style.transform = '', 180);
}

/* ── HELPERS ─────────────────────────────────────────────── */
function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

/* ── DEMO DATA (fallback) ────────────────────────────────── */
function getDemoProducts() {
  return [
    { id:1, name:'Wireless Headphones', category:'Audio', price:89.99, description:'Premium over-ear headphones with 30hr battery and active noise cancellation.', emoji:'🎧', stock:10 },
    { id:2, name:'Mechanical Keyboard', category:'Peripherals', price:129.99, description:'Tactile switches, RGB backlight, and a compact tenkeyless layout.', emoji:'⌨️', stock:5 },
    { id:3, name:'USB-C Hub', category:'Accessories', price:39.99, description:'7-in-1 hub: HDMI 4K, 3× USB-A, SD card, PD charging, and Ethernet.', emoji:'🔌', stock:20 },
    { id:4, name:'Standing Desk Mat', category:'Ergonomics', price:59.99, description:'Anti-fatigue mat with beveled edges for all-day comfort.', emoji:'🟫', stock:8 },
    { id:5, name:'Webcam 4K', category:'Video', price:109.99, description:'Auto-focus 4K camera with built-in ring light for crisp video calls.', emoji:'📷', stock:3 },
    { id:6, name:'Laptop Stand', category:'Accessories', price:49.99, description:'Adjustable aluminium stand, folds flat, and fits any 10–17" laptop.', emoji:'💻', stock:15 },
  ];
}