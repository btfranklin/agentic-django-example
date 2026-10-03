(() => {
  const form = document.querySelector("[data-agent-form]");
  const textarea = form ? form.querySelector("textarea[name='input']") : null;

  if (form && textarea) {
    let submittedValue = null;
    const error = document.getElementById("request-error");

    function showError(message) {
      error.textContent = message;
      error.hidden = false;
    }

    form.addEventListener("htmx:beforeRequest", (event) => {
      if (event.detail && event.detail.elt === form) {
        submittedValue = textarea.value;
        error.textContent = "";
        error.hidden = true;
      }
    });

    form.addEventListener("htmx:beforeOnLoad", (event) => {
      if (event.detail.elt !== form || event.detail.xhr.status < 400) {
        return;
      }
      // Keep the debug helper from replacing the form with an error document.
      event.stopPropagation();
      let message = "The request failed. Check the run status before you try again.";
      try {
        const response = JSON.parse(event.detail.xhr.responseText);
        if (typeof response.error === "string" && response.error) {
          message = response.error;
        }
      } catch {
        // HTML error pages stay in the server logs.
      }
      showError(message);
    });

    form.addEventListener("htmx:afterRequest", (event) => {
      if (!event.detail || event.detail.elt !== form) {
        return;
      }
      if (event.detail.successful !== true) {
        if (error.hidden) {
          showError("The request did not finish. Check the run status before you try again.");
        }
        return;
      }

      if (submittedValue !== null && textarea.value === submittedValue) {
        textarea.value = "";
      }
      submittedValue = null;
    });
  }

})();
