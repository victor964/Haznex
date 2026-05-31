(function () {
  "use strict";

  function formatKes(amount) {
    if (amount == null) return "N/A";
    return "KES " + Math.round(amount).toLocaleString("en-KE");
  }

  function initPlaceOrderTotal() {
    var dataEl = document.getElementById("place-order-data");
    if (!dataEl) return;

    var data;
    try {
      data = JSON.parse(dataEl.textContent);
    } catch (e) {
      return;
    }

    var radios = document.querySelectorAll(".shipping-radio");
    var shippingEl = document.getElementById("selected-shipping-cost");
    var totalEl = document.getElementById("order-total");

    function updateTotal() {
      var selected = document.querySelector(".shipping-radio:checked");
      if (!selected || !data.unitPrice) return;
      var shippingCost = data.shippingCosts[selected.value];
      if (shippingEl) shippingEl.textContent = formatKes(shippingCost);
      if (totalEl) totalEl.textContent = formatKes(data.unitPrice + (shippingCost || 0));
    }

    radios.forEach(function (radio) {
      radio.addEventListener("change", updateTotal);
    });
    updateTotal();
  }

  document.addEventListener("DOMContentLoaded", initPlaceOrderTotal);
})();
