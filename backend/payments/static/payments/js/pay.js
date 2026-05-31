(function () {
  const config = window.HAZNEX_PAY;
  if (!config) return;

  const form = document.getElementById("pay-form");
  const phoneInput = document.getElementById("phone_number");
  const payBtn = document.getElementById("pay-now-btn");
  const messageEl = document.getElementById("pay-message");
  const manualForm = document.getElementById("manual-form");
  const manualPhone = document.getElementById("manual_phone_number");

  if (!form || !phoneInput || !payBtn) return;

  const defaultBtnHtml = payBtn.innerHTML;

  if (manualForm && manualPhone) {
    manualForm.addEventListener("submit", function () {
      manualPhone.value = phoneInput.value.trim();
    });
  }

  function showMessage(text, isError) {
    if (!messageEl) return;
    messageEl.textContent = text;
    messageEl.classList.remove("hidden", "text-red-600", "text-gold-dark");
    messageEl.classList.add(isError ? "text-red-600" : "text-gold-dark");
  }

  function setLoading(isLoading) {
    if (isLoading) {
      payBtn.disabled = true;
      payBtn.innerHTML =
        '<span class="inline-flex items-center justify-center gap-2">' +
        '<svg class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
        '<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>' +
        '<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>' +
        "</svg>Processing…</span>";
    } else {
      payBtn.disabled = false;
      payBtn.innerHTML = defaultBtnHtml;
    }
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const phone = phoneInput.value.trim();
    if (!phone) {
      showMessage("Please enter your M-Pesa phone number.", true);
      return;
    }

    const csrf = form.querySelector("[name=csrfmiddlewaretoken]");
    if (!csrf) return;

    setLoading(true);

    try {
      const body = new FormData();
      body.append("phone_number", phone);
      body.append("csrfmiddlewaretoken", csrf.value);

      const res = await fetch(config.initiateUrl, {
        method: "POST",
        body: body,
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });

      const data = await res.json();

      if (data.success) {
        showMessage(data.message || "Check your phone for the M-Pesa prompt.", false);
      } else if (data.reason === "stk_disabled") {
        setLoading(false);
        showMessage(
          "STK Push is not enabled. Pay via M-Pesa, then use “I Have Paid” below.",
          false
        );
      } else {
        setLoading(false);
        showMessage(
          data.error || "Could not initiate payment. Please try the manual confirmation.",
          true
        );
      }
    } catch (err) {
      setLoading(false);
      showMessage(
        "Could not initiate payment. Please try the manual confirmation.",
        true
      );
    }
  });
})();
