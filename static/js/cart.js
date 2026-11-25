/* Shopping Cart: quantity updates, removal, checkout simulation, and live Apriori recommendations */

function renderCartView(data) {
  updateCartBadge(data.item_count || 0);

  const itemsContainer = document.getElementById("cartItemsContainer");
  const summaryContainer = document.getElementById("cartSummaryContainer");
  const recContainer = document.getElementById("cartRecsContainer");

  if (!itemsContainer || !summaryContainer) return;

  if (!data.items || !data.items.length) {
    itemsContainer.innerHTML = `
      <div style="padding: 48px 24px; text-align: center;">
        <h3 style="margin-bottom: 8px;">Your shopping cart is empty</h3>
        <p style="color: var(--slate-500); margin-bottom: 20px;">Explore our 36 products and add items to see real-time Apriori recommendations.</p>
        <a href="/products" class="btn btn-primary">Explore Products</a>
      </div>
    `;
    summaryContainer.innerHTML = `
      <h3 style="margin-bottom: 14px;">Order Summary</h3>
      <div class="summary-row"><span>Items</span><span>0</span></div>
      <div class="summary-row"><span>Subtotal</span><span>$0.00</span></div>
      <div class="summary-row"><span>Estimated Tax (5%)</span><span>$0.00</span></div>
      <div class="summary-total"><span>Total</span><span>$0.00</span></div>
      <button class="btn btn-primary" style="width:100%; margin-top:18px; opacity:0.55; cursor:not-allowed;" disabled>Complete Checkout</button>
    `;
    if (recContainer) {
      recContainer.innerHTML = `<p style="color: var(--slate-500); margin:0;">${data.rec_message || "Add items to see AI basket suggestions."}</p>`;
    }
    return;
  }

  itemsContainer.innerHTML = data.items
    .map(
      (item) => `
    <div class="cart-item">
      <img src="${item.image_path}" alt="${item.name}" />
      <div style="flex:1; min-width: 150px;">
        <div style="font-size:0.75rem; font-weight:600; color:var(--accent-primary);">${item.category}</div>
        <div style="font-weight:700; font-size:1.02rem;">${item.name}</div>
        <div style="font-size:0.84rem; color:var(--slate-500);">$${Number(item.price).toFixed(2)} / ${item.unit}</div>
      </div>
      <div class="qty-control">
        <button onclick="updateCartQty(${item.id}, ${item.quantity - 1})" aria-label="Decrease quantity">-</button>
        <span>${item.quantity}</span>
        <button onclick="updateCartQty(${item.id}, ${item.quantity + 1})" aria-label="Increase quantity">+</button>
      </div>
      <div style="min-width: 78px; text-align:right; font-weight:800;">$${Number(item.line_total).toFixed(2)}</div>
      <button class="btn btn-danger-soft btn-sm" onclick="removeCartItem(${item.id})">Remove</button>
    </div>
  `
    )
    .join("");

  summaryContainer.innerHTML = `
    <h3 style="margin-bottom: 14px;">Order Summary</h3>
    <div class="summary-row"><span>Total Items</span><span>${data.item_count}</span></div>
    <div class="summary-row"><span>Subtotal</span><span>$${Number(data.subtotal).toFixed(2)}</span></div>
    <div class="summary-row"><span>Estimated Tax (5%)</span><span>$${Number(data.tax).toFixed(2)}</span></div>
    <div class="summary-total"><span>Total</span><span>$${Number(data.total).toFixed(2)}</span></div>
    <button id="checkoutBtn" class="btn btn-primary btn-lg" style="width:100%; margin-top:18px;" onclick="checkoutOrder()">
      Complete Checkout
    </button>
    <button class="btn btn-ghost btn-sm" style="width:100%; margin-top:8px;" onclick="clearCart()">Clear Cart</button>
  `;

  if (recContainer) {
    if (data.recommendations && data.recommendations.length) {
      recContainer.innerHTML = `
        <div class="rec-grid">
          ${data.recommendations
            .map(
              (r) => `
            <div class="rec-card">
              <div class="rec-top">
                <img src="${r.product.image_path}" alt="${r.product.name}" />
                <div>
                  <div style="font-weight:700;">${r.product.name}</div>
                  <div style="font-size:0.84rem; color:var(--slate-500);">$${Number(r.product.price).toFixed(2)} · ${r.product.category}</div>
                </div>
              </div>
              <div class="rec-explanation">${r.explanation}</div>
              <div class="metrics-row">
                <div class="metric-chip"><strong>${r.confidence_pct}%</strong><span>Confidence</span></div>
                <div class="metric-chip"><strong>${r.support_pct}%</strong><span>Support</span></div>
                <div class="metric-chip"><strong>${r.lift}x</strong><span>Lift</span></div>
              </div>
              <button class="btn btn-outline btn-sm" onclick="addRecommendedToCart(${r.product.id})">+ Add to Cart</button>
            </div>
          `
            )
            .join("")}
        </div>
      `;
    } else {
      recContainer.innerHTML = `<div class="alert alert-info" style="margin:0;">${data.rec_message || "No additional recommendations found for your current basket."}</div>`;
    }
  }
}

async function updateCartQty(productId, newQty) {
  const res = await fetch("/api/cart/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, quantity: newQty }),
  });
  const data = await res.json();
  if (res.ok) renderCartView(data);
}

async function removeCartItem(productId) {
  const res = await fetch("/api/cart/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId }),
  });
  const data = await res.json();
  if (res.ok) {
    renderCartView(data);
    showToast("Item removed from cart");
  }
}

async function clearCart() {
  const res = await fetch("/api/cart/clear", { method: "POST" });
  const data = await res.json();
  if (res.ok) {
    renderCartView(data);
    showToast("Cart cleared");
  }
}

async function addRecommendedToCart(productId) {
  const data = await addToCart(productId, 1);
  if (data) renderCartView(data);
}

async function checkoutOrder() {
  const btn = document.getElementById("checkoutBtn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Processing Order & Updating ML...";
  }
  try {
    const res = await fetch("/api/checkout", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || "Checkout failed", true);
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Complete Checkout";
      }
      return;
    }

    renderCartView(data.cart);
    const receiptBox = document.getElementById("checkoutReceipt");
    if (receiptBox && data.order) {
      receiptBox.style.display = "block";
      receiptBox.innerHTML = `
        <div class="alert alert-success" style="margin-bottom:0;">
          <strong>Order Confirmed!</strong> Transaction <code>${data.order.transaction_code}</code>
          for <strong>$${Number(data.order.total_amount).toFixed(2)}</strong> (${data.order.item_count} items)
          has been saved to SQLite, and the Apriori recommendation model has been retrained!
          <div style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;">
            <a href="/dashboard" class="btn btn-sm btn-primary">View Updated Analytics</a>
            <a href="/products" class="btn btn-sm btn-outline">Continue Shopping</a>
          </div>
        </div>
      `;
    }
    showToast("Checkout complete! Transaction saved.");
  } catch (err) {
    showToast("Network error during checkout.", true);
  }
}
