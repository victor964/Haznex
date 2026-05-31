(function () {
  "use strict";

  function initProductListAnimations() {
    if (typeof gsap === "undefined") return;

    var cards = document.querySelectorAll(".product-card");
    if (!cards.length) return;

    gsap.from(cards, {
      opacity: 0,
      y: 30,
      duration: 0.5,
      stagger: 0.08,
      ease: "power2.out",
    });
  }

  document.addEventListener("DOMContentLoaded", initProductListAnimations);
})();
