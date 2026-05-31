(function () {
  const input = document.getElementById("id_images");
  const container = document.getElementById("image-preview-container");
  if (!input || !container) return;

  input.addEventListener("change", function () {
    container.innerHTML = "";
    Array.from(input.files).forEach((file, index) => {
      if (!file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = function (e) {
        const wrap = document.createElement("div");
        wrap.className = "haznex-preview-item";
        wrap.innerHTML =
          '<img src="' +
          e.target.result +
          '" alt="Preview ' +
          (index + 1) +
          '"><span>#' +
          index +
          "</span>";
        container.appendChild(wrap);
      };
      reader.readAsDataURL(file);
    });
  });
})();
