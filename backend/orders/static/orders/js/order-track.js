(function () {
  "use strict";

  function initTimelineAnimation() {
    if (typeof gsap === "undefined") return;

    var steps = document.querySelectorAll(".timeline-step");
    if (!steps.length) return;

    gsap.set(steps, { opacity: 0, x: -20 });

    gsap.to(steps, {
      opacity: 1,
      x: 0,
      duration: 0.5,
      stagger: 0.15,
      ease: "power2.out",
    });
  }

  document.addEventListener("DOMContentLoaded", initTimelineAnimation);
})();
