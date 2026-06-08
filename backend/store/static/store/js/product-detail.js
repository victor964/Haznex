(function () {
  "use strict";

  var SLIDESHOW_INTERVAL_MS = 4000;

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
    var mainImage = document.getElementById("main-image");
    var thumbnails = Array.prototype.slice.call(document.querySelectorAll(".thumbnail-btn"));
    if (!mainImage || thumbnails.length < 2) return;

    var galleryEl = document.getElementById("product-gallery");
    var currentIndex = thumbnails.findIndex(function (btn) {
      return btn.classList.contains("border-gold");
    });
    if (currentIndex < 0) currentIndex = 0;

    var slideshowTimer = null;
    var hasGsap = typeof gsap !== "undefined";

    function setActiveThumbnail(index) {
      thumbnails.forEach(function (btn, i) {
        btn.classList.toggle("border-gold", i === index);
        btn.classList.toggle("border-haznex-border", i !== index);
      });
    }

    function swapMainImage(newUrl, animate) {
      if (!animate || !hasGsap) {
        mainImage.src = newUrl;
        return;
      }

      gsap.to(mainImage, {
        opacity: 0,
        duration: 0.2,
        onComplete: function () {
          mainImage.src = newUrl;
          gsap.to(mainImage, { opacity: 1, duration: 0.3 });
        },
      });
    }

    function showImage(index, animate) {
      var btn = thumbnails[index];
      if (!btn) return;

      var newUrl = btn.getAttribute("data-image-url");
      if (!newUrl) return;

      currentIndex = index;
      setActiveThumbnail(index);
      btn.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
      swapMainImage(newUrl, animate);
    }

    function nextImage() {
      showImage((currentIndex + 1) % thumbnails.length, true);
    }

    function startSlideshow() {
      stopSlideshow();
      slideshowTimer = window.setInterval(nextImage, SLIDESHOW_INTERVAL_MS);
    }

    function stopSlideshow() {
      if (slideshowTimer) {
        window.clearInterval(slideshowTimer);
        slideshowTimer = null;
      }
    }

    thumbnails.forEach(function (btn, index) {
      btn.addEventListener("click", function () {
        stopSlideshow();
        showImage(index, true);
        startSlideshow();
      });
    });

    if (galleryEl) {
      galleryEl.addEventListener("mouseenter", stopSlideshow);
      galleryEl.addEventListener("mouseleave", startSlideshow);
      galleryEl.addEventListener("focusin", stopSlideshow);
      galleryEl.addEventListener("focusout", function (event) {
        if (!galleryEl.contains(event.relatedTarget)) {
          startSlideshow();
        }
      });
    }

    startSlideshow();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initShippingTotal();
    initGalleryCrossfade();
  });
})();
