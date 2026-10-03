(() => {
  const form = document.querySelector("[data-agent-form]");
  const textarea = form ? form.querySelector("textarea[name='input']") : null;

  if (form && textarea) {
    let submittedValue = null;

    form.addEventListener("htmx:beforeRequest", (event) => {
      if (event.detail && event.detail.elt === form) {
        submittedValue = textarea.value;
      }
    });

    form.addEventListener("htmx:afterRequest", (event) => {
      if (
        !event.detail ||
        event.detail.elt !== form ||
        event.detail.successful !== true
      ) {
        return;
      }

      if (submittedValue !== null && textarea.value === submittedValue) {
        textarea.value = "";
      }
      submittedValue = null;
    });
  }

})();
