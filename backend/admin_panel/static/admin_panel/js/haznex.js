(function () {
  "use strict";

  function initMobileNav() {
    var menuBtn = document.getElementById("haznex-menu-btn");
    var sidebar = document.getElementById("haznex-sidebar");
    var overlay = document.getElementById("haznex-sidebar-overlay");
    if (!menuBtn || !sidebar || !overlay) {
      return;
    }

    function openMenu() {
      sidebar.classList.add("is-open");
      overlay.hidden = false;
      menuBtn.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
    }

    function closeMenu() {
      sidebar.classList.remove("is-open");
      overlay.hidden = true;
      menuBtn.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    }

    menuBtn.addEventListener("click", function () {
      if (sidebar.classList.contains("is-open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    overlay.addEventListener("click", closeMenu);

    document.querySelectorAll(".haznex-nav-link").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });

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

    window.addEventListener("resize", function () {
      if (window.innerWidth >= 768) {
        closeMenu();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initMobileNav);
})();
