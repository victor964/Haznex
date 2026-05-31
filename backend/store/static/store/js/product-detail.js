(function () {
  "use strict";

  function formatKes(amount) {
    if (amount == null) return "N/A";
    return "KES " + Math.round(amount).toLocaleString("en-KE");
  }

  function initShippingTotal() {
    var dataEl = document.getElementById("product-detail-data");
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
      if (!selected || !data.unitPrice) {
        if (shippingEl) shippingEl.textContent = "N/A";
        if (totalEl) totalEl.textContent = "N/A";
        return;
      }
      var shippingCost = data.shippingCosts[selected.value];
      if (shippingEl) shippingEl.textContent = formatKes(shippingCost);
      if (totalEl) totalEl.textContent = formatKes(data.unitPrice + (shippingCost || 0));
    }

    radios.forEach(function (radio) {
      radio.addEventListener("change", updateTotal);
    });
    updateTotal();
  }

  function initGalleryCrossfade() {
    if (typeof gsap === "undefined") return;

    var mainImage = document.getElementById("main-image");
    var thumbnails = document.querySelectorAll(".thumbnail-btn");
    if (!mainImage || !thumbnails.length) return;

    thumbnails.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var newUrl = btn.getAttribute("data-image-url");
        if (!newUrl || mainImage.src === newUrl) return;

        thumbnails.forEach(function (b) {
          b.classList.remove("border-gold");
          b.classList.add("border-haznex-border");
        });
        btn.classList.remove("border-haznex-border");
        btn.classList.add("border-gold");

        gsap.to(mainImage, {
          opacity: 0,
          duration: 0.2,
          onComplete: function () {
            mainImage.src = newUrl;
            gsap.to(mainImage, { opacity: 1, duration: 0.3 });
          },
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initShippingTotal();
    initGalleryCrossfade();
  });
})();
