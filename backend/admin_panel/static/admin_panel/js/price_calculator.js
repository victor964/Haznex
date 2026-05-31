/**
 * Haznex price calculator: sum all GBP fields (including uk_original_price),
 * multiply by GBP_TO_KES rate, set final_client_price in KES.
 */
document.addEventListener("DOMContentLoaded", function () {
  const form =
    document.getElementById("pricing-form") ||
    document.getElementById("product-edit-form");
  if (!form) return;

  const rate = parseFloat(
    window.HAZNEX_GBP_TO_KES || form.getAttribute("data-gbp-to-kes-rate") || "165"
  );

  const GBP_FIELD_NAMES = [
    "uk_original_price",
    "sourcing_fee",
    "shipping_cost",
    "transport_logistics_cost",
    "profit_margin",
  ];

  const gbpSubtotalEl = document.getElementById("gbp-subtotal-display");
  const displayEl = document.getElementById("final-price-display");
  const finalInput = form.querySelector('[name="final_client_price"]');
  const rateHintEl = document.getElementById("exchange-rate-hint");

  function getGbpInputs() {
    return GBP_FIELD_NAMES.map(function (name) {
      return form.querySelector('[name="' + name + '"]');
    }).filter(Boolean);
  }

  function recalculate() {
    let gbpSum = 0;
    getGbpInputs().forEach(function (el) {
      const val = parseFloat(el.value);
      if (Number.isFinite(val)) gbpSum += val;
    });

    const kesTotal = (gbpSum * rate).toFixed(2);
    const gbpFormatted = gbpSum.toFixed(2);

    if (gbpSubtotalEl) gbpSubtotalEl.textContent = gbpFormatted + " GBP";
    if (displayEl) displayEl.textContent = kesTotal + " KES";
    if (finalInput) finalInput.value = kesTotal;
    if (rateHintEl) rateHintEl.textContent = "1 GBP = " + rate + " KES";
  }

  GBP_FIELD_NAMES.forEach(function (name) {
    const el = form.querySelector('[name="' + name + '"]');
    if (el) el.classList.add("haznex-gbp-field");
  });

  form.addEventListener("input", function (e) {
    if (e.target && e.target.name && GBP_FIELD_NAMES.indexOf(e.target.name) !== -1) {
      recalculate();
    }
  });

  form.addEventListener("change", function (e) {
    if (e.target && e.target.name && GBP_FIELD_NAMES.indexOf(e.target.name) !== -1) {
      recalculate();
    }
  });

  recalculate();
});
