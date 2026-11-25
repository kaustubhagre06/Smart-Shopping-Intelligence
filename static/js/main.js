/* Global UI helpers: mobile navigation, toast notifications, and cart badge updates */

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }
});

function showToast(message, isError = false) {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = "toast";
  if (isError) {
    toast.style.background = "#B91C1C";
  }
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.2s ease";
    setTimeout(() => toast.remove(), 220);
  }, 2600);
}

function updateCartBadge(count) {
  const badge = document.getElementById("navCartBadge");
  if (badge) {
    badge.textContent = count;
  }
}

async function addToCart(productId, quantity = 1) {
  try {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || "Could not add item to cart.", true);
      return null;
    }
    updateCartBadge(data.item_count);
    showToast(`Added ${data.added_product || "item"} to cart`);
    return data;
  } catch (err) {
    showToast("Network error while adding to cart.", true);
    return null;
  }
}
