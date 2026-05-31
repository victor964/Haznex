(function () {
  "use strict";

  if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
  }

  function initMobileNav() {
    var menuBtn = document.getElementById("mobile-menu-btn");
    var menuClose = document.getElementById("mobile-menu-close");
    var menu = document.getElementById("mobile-menu");
    var overlay = document.getElementById("mobile-menu-overlay");
    var iconOpen = document.getElementById("menu-icon-open");
    var iconClose = document.getElementById("menu-icon-close");

    if (!menuBtn || !menu || !overlay || typeof gsap === "undefined") {
      return;
    }

    var isOpen = false;

    function openMenu() {
      isOpen = true;
      overlay.classList.remove("hidden");
      menuBtn.setAttribute("aria-expanded", "true");
      if (iconOpen) iconOpen.classList.add("hidden");
      if (iconClose) iconClose.classList.remove("hidden");

      gsap.set(overlay, { opacity: 0 });
      gsap.set(menu, { x: "100%" });

      gsap.to(overlay, { opacity: 1, duration: 0.25, ease: "power2.out" });
      gsap.to(menu, { x: "0%", duration: 0.35, ease: "power2.out" });
    }

    function closeMenu() {
      if (!isOpen) return;
      isOpen = false;
      menuBtn.setAttribute("aria-expanded", "false");
      if (iconOpen) iconOpen.classList.remove("hidden");
      if (iconClose) iconClose.classList.add("hidden");

      gsap.to(overlay, {
        opacity: 0,
        duration: 0.2,
        ease: "power2.in",
        onComplete: function () {
          overlay.classList.add("hidden");
        },
      });
      gsap.to(menu, { x: "100%", duration: 0.3, ease: "power2.in" });
    }

    menuBtn.addEventListener("click", function () {
      if (isOpen) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    if (menuClose) {
      menuClose.addEventListener("click", closeMenu);
    }

    overlay.addEventListener("click", closeMenu);

    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });
  }

  function initFormSubmitGuard() {
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function () {
        form.querySelectorAll('[type="submit"]').forEach(function (btn) {
          if (btn.disabled) {
            return;
          }
          btn.disabled = true;
          if (!btn.dataset.originalText) {
            btn.dataset.originalText = btn.textContent.trim();
          }
          btn.textContent = "Processing...";
        });
      });
    });
  }

  function initPageLoader() {
    var loader = document.getElementById("page-loader");
    if (!loader) {
      return;
    }

    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion || typeof gsap === "undefined") {
      loader.style.display = "none";
      return;
    }

    var finished = false;

    function finishLoader() {
      if (finished) {
        return;
      }
      finished = true;
      gsap.to(loader, {
        width: "100%",
        duration: 0.2,
        ease: "power2.out",
        onComplete: function () {
          gsap.to(loader, {
            opacity: 0,
            duration: 0.25,
            onComplete: function () {
              loader.remove();
            },
          });
        },
      });
    }

    gsap.set(loader, { width: "0%" });
    gsap.to(loader, {
      width: "30%",
      duration: 0.3,
      ease: "power2.out",
      onComplete: function () {
        gsap.to(loader, {
          width: "70%",
          duration: 1.5,
          ease: "none",
        });
      },
    });

    if (document.readyState === "complete") {
      finishLoader();
    } else {
      window.addEventListener("load", finishLoader);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initMobileNav();
    initFormSubmitGuard();
    initPageLoader();
  });
})();
