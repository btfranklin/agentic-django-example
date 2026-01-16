(() => {
  const form = document.querySelector("[data-agent-form]");
  const textarea = form ? form.querySelector("textarea[name='input']") : null;

  if (form && textarea) {
    form.addEventListener("htmx:beforeRequest", () => {
      form.dataset.lastRequest = textarea.value.trim();
    });

    form.addEventListener("htmx:afterRequest", (event) => {
      if (event.detail && event.detail.failed) {
        return;
      }
      textarea.value = "";
      form.dataset.lastRequest = "";
    });
  }

})();
