/* Product Explorer: live search, category pills, sort, and AI-powered Product Detail Modal */

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("productSearch");
  const sortSelect = document.getElementById("productSort");
  const pillButtons = document.querySelectorAll(".pill-btn[data-category]");
  const productGrid = document.getElementById("productGrid");
  const resultCount = document.getElementById("productResultCount");

  if (!productGrid) return;

  let activeCategory = productGrid.dataset.initialCategory || "All";
  let debounceTimer = null;

  function renderProducts(products) {
    if (resultCount) {
      resultCount.textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;
    }

    if (!products.length) {
      productGrid.innerHTML = `
        <div class="card card-padded" style="grid-column: 1 / -1; text-align: center; padding: 48px 24px;">
          <h3 style="margin-bottom: 8px;">No matching products found</h3>
          <p style="color: var(--slate-500); margin-bottom: 18px;">Try clearing your search term or selecting All categories.</p>
          <button class="btn btn-outline" onclick="resetExplorerFilters()">Reset Filters</button>
        </div>
      `;
      return;
    }

    productGrid.innerHTML = products
      .map(
        (p) => `
      <article class="product-card" data-product-id="${p.id}">
        <div class="product-img-wrap" onclick="openProductModal(${p.id})" title="View details & AI recommendations">
          <span class="product-badge">${p.badge}</span>
          <img src="${p.image_path}" alt="${p.name}" loading="lazy" />
        </div>
        <div class="product-cat">${p.category}</div>
        <h3 class="product-name">
          <a href="/product/${p.id}" onclick="event.preventDefault(); openProductModal(${p.id});">${p.name}</a>
        </h3>
        <div class="product-unit">${p.unit} · ★ ${Number(p.rating).toFixed(1)}</div>
        <div class="product-footer">
          <span class="product-price">$${Number(p.price).toFixed(2)}</span>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline btn-sm" onclick="openProductModal(${p.id})">Details</button>
            <button class="btn btn-primary btn-sm" onclick="addToCart(${p.id}, 1)">+ Add</button>
          </div>
        </div>
      </article>
    `
      )
      .join("");
  }

  async function fetchFilteredProducts() {
    const q = searchInput ? searchInput.value.trim() : "";
    const sort = sortSelect ? sortSelect.value : "featured";
    const params = new URLSearchParams({
      q,
      category: activeCategory,
      sort,
    });
    const res = await fetch(`/api/products?${params.toString()}`);
    if (!res.ok) return;
    const data = await res.json();
    renderProducts(data.products || []);
  }

  window.resetExplorerFilters = () => {
    if (searchInput) searchInput.value = "";
    if (sortSelect) sortSelect.value = "featured";
    activeCategory = "All";
    pillButtons.forEach((b) => b.classList.toggle("active", b.dataset.category === "All"));
    fetchFilteredProducts();
  };

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchFilteredProducts, 200);
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", fetchFilteredProducts);
  }

  pillButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      activeCategory = btn.dataset.category;
      pillButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      fetchFilteredProducts();
    });
  });
});

async function openProductModal(productId) {
  const modal = document.getElementById("productModal");
  const body = document.getElementById("productModalBody");
  if (!modal || !body) {
    window.location.href = `/product/${productId}`;
    return;
  }

  body.innerHTML = `<p style="padding: 32px; text-align: center; color: var(--slate-500);">Loading product details & Apriori recommendations...</p>`;
  modal.classList.add("open");

  try {
    const res = await fetch(`/api/products/${productId}`);
    const data = await res.json();
    if (!res.ok) {
      body.innerHTML = `<p class="alert alert-danger">${data.error || "Product not found."}</p>`;
      return;
    }

    const p = data.product;
    const recs = data.recommendations || [];

    const recHtml = recs.length
      ? `
        <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--border-color);">
          <h3 style="font-size: 1.05rem; margin-bottom: 12px;">Smart Recommendations (Apriori ML)</h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
            ${recs
              .map(
                (r) => `
              <div class="card" style="padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display:flex; align-items:center; gap: 10px;">
                  <img src="${r.product.image_path}" alt="${r.product.name}" style="width:44px;height:44px;border-radius:8px;background:var(--bg-page);padding:3px;" />
                  <div>
                    <div style="font-weight:700; font-size:0.92rem;">${r.product.name}</div>
                    <div style="font-size:0.8rem; color:var(--slate-500);">$${Number(r.product.price).toFixed(2)} · Lift ${r.lift}x</div>
                  </div>
                </div>
                <div style="font-size:0.8rem; color:var(--navy-700); background:var(--accent-soft); padding:7px 9px; border-radius:7px;">
                  ${r.explanation} (${r.confidence_pct}% conf.)
                </div>
                <button class="btn btn-outline btn-sm" onclick="addToCart(${r.product.id}, 1)">+ Add ${r.product.name}</button>
              </div>
            `
              )
              .join("")}
          </div>
        </div>
      `
      : `<p style="margin-top:20px; font-size:0.88rem; color:var(--slate-500);">${data.message || "No pair recommendations meet current thresholds."}</p>`;

    body.innerHTML = `
      <div style="display:grid; grid-template-columns: 200px 1fr; gap: 24px; align-items: center;">
        <div style="background: var(--bg-page); border-radius: 16px; padding: 18px; text-align:center;">
          <img src="${p.image_path}" alt="${p.name}" style="max-height:170px; margin:0 auto;" />
        </div>
        <div>
          <span class="badge">${p.category}</span>
          <h2 style="margin: 10px 0 6px; font-size: 1.65rem;">${p.name}</h2>
          <p style="color: var(--slate-500); font-size: 0.9rem; margin: 0 0 12px;">${p.unit} · ★ ${Number(p.rating).toFixed(1)} · ${p.badge}</p>
          <p style="color: var(--navy-700); font-size: 0.95rem; margin-bottom: 18px;">${p.description}</p>
          <div style="display:flex; align-items:center; gap: 14px; flex-wrap:wrap;">
            <span style="font-size: 1.55rem; font-weight: 800;">$${Number(p.price).toFixed(2)}</span>
            <button class="btn btn-primary" onclick="addToCart(${p.id}, 1)">Add to Cart</button>
            <a href="/product/${p.id}" class="btn btn-outline">Full Page</a>
          </div>
        </div>
      </div>
      ${recHtml}
    `;
  } catch (err) {
    body.innerHTML = `<p class="alert alert-danger">Failed to load product details.</p>`;
  }
}

function closeProductModal() {
  const modal = document.getElementById("productModal");
  if (modal) modal.classList.remove("open");
}
