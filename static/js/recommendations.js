/* Smart Recommendation Engine Workbench: interactive product selection + Apriori parameter tuning */

document.addEventListener("DOMContentLoaded", () => {
  const chips = document.querySelectorAll(".item-chip[data-item]");
  const runBtn = document.getElementById("runRecommendBtn");
  const clearBtn = document.getElementById("clearSelectionBtn");
  const supportSlider = document.getElementById("supportSlider");
  const confSlider = document.getElementById("confSlider");
  const supportLabel = document.getElementById("supportValue");
  const confLabel = document.getElementById("confValue");
  const resultsContainer = document.getElementById("recommenderResults");
  const selectedLabel = document.getElementById("selectedItemsLabel");
  const rulesTableBody = document.getElementById("rulesTableBody");

  if (!chips.length || !resultsContainer) return;

  function getSelectedItems() {
    return Array.from(chips)
      .filter((c) => c.classList.contains("selected"))
      .map((c) => c.dataset.item);
  }

  function updateSelectedBadge() {
    const items = getSelectedItems();
    if (selectedLabel) {
      selectedLabel.textContent = items.length ? items.join(", ") : "None selected";
    }
  }

  async function runRecommendations() {
    const items = getSelectedItems();
    const minSupport = supportSlider ? parseFloat(supportSlider.value) : 0.025;
    const minConfidence = confSlider ? parseFloat(confSlider.value) : 0.25;

    resultsContainer.innerHTML = `<div class="card card-padded" style="text-align:center; color:var(--slate-500);">Mining frequent itemsets & evaluating association rules...</div>`;

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items,
          min_support: minSupport,
          min_confidence: minConfidence,
          top_n: 6,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error || "Failed to generate recommendations."}</div>`;
        return;
      }

      // Update model stats summary pills
      const statRules = document.getElementById("statRulesCount");
      const statItemsets = document.getElementById("statItemsetsCount");
      if (statRules && data.model_summary) statRules.textContent = data.model_summary.rules_count;
      if (statItemsets && data.model_summary) statItemsets.textContent = data.model_summary.frequent_itemsets_count;

      if (!data.recommendations || !data.recommendations.length) {
        resultsContainer.innerHTML = `
          <div class="card card-padded" style="text-align:center; padding: 36px 24px;">
            <h3 style="margin-bottom: 8px;">No Matching Association Rules</h3>
            <p style="color: var(--slate-500); margin: 0;">${data.message || "Try selecting another product or lowering the support/confidence sliders."}</p>
          </div>
        `;
      } else {
        resultsContainer.innerHTML = `
          <div class="rec-grid">
            ${data.recommendations
              .map(
                (r) => `
              <div class="rec-card">
                <div class="rec-top">
                  <img src="${r.product.image_path}" alt="${r.product.name}" />
                  <div>
                    <div class="badge" style="margin-bottom:4px;">${r.product.category}</div>
                    <div style="font-weight:700; font-size:1.05rem;">${r.product.name}</div>
                    <div style="font-size:0.84rem; color:var(--slate-500);">$${Number(r.product.price).toFixed(2)} · ${r.product.unit}</div>
                  </div>
                </div>
                <div class="rec-explanation">${r.explanation}</div>
                <div class="metrics-row">
                  <div class="metric-chip"><strong>${r.confidence_pct}%</strong><span>Confidence</span></div>
                  <div class="metric-chip"><strong>${r.support_pct}%</strong><span>Support</span></div>
                  <div class="metric-chip"><strong>${r.lift}x</strong><span>Lift</span></div>
                </div>
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-primary btn-sm" style="flex:1;" onclick="addToCart(${r.product.id}, 1)">+ Add to Cart</button>
                  <a class="btn btn-outline btn-sm" href="/product/${r.product.id}">Inspect</a>
                </div>
              </div>
            `
              )
              .join("")}
          </div>
        `;
      }

      if (rulesTableBody && data.top_rules) {
        rulesTableBody.innerHTML = data.top_rules.length
          ? data.top_rules
              .map(
                (rule) => `
              <tr>
                <td><strong>${rule.antecedents}</strong></td>
                <td><span class="badge">${rule.consequents}</span></td>
                <td>${rule.support_pct}%</td>
                <td>${rule.confidence_pct}%</td>
                <td><strong>${rule.lift}x</strong></td>
                <td style="color:var(--slate-500); font-size:0.83rem;">${rule.explanation}</td>
              </tr>
            `
              )
              .join("")
          : `<tr><td colspan="6" style="text-align:center; color:var(--slate-500);">No rules generated at current thresholds.</td></tr>`;
      }
    } catch (err) {
      resultsContainer.innerHTML = `<div class="alert alert-danger">Network error communicating with Apriori API.</div>`;
    }
  }

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chip.classList.toggle("selected");
      updateSelectedBadge();
      runRecommendations();
    });
  });

  if (supportSlider && supportLabel) {
    supportSlider.addEventListener("input", () => {
      supportLabel.textContent = `${(parseFloat(supportSlider.value) * 100).toFixed(1)}%`;
    });
  }

  if (confSlider && confLabel) {
    confSlider.addEventListener("input", () => {
      confLabel.textContent = `${Math.round(parseFloat(confSlider.value) * 100)}%`;
    });
  }

  if (runBtn) {
    runBtn.addEventListener("click", runRecommendations);
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("selected"));
      updateSelectedBadge();
      runRecommendations();
    });
  }

  window.selectPresetBasket = (items) => {
    const set = new Set(items);
    chips.forEach((c) => c.classList.toggle("selected", set.has(c.dataset.item)));
    updateSelectedBadge();
    runRecommendations();
  };
});
