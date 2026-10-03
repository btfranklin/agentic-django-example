const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const appScript = fs.readFileSync(
  path.join(__dirname, "../../static/sample_app/app.js"),
  "utf8",
);

function createFormPage() {
  const listeners = new Map();
  const textarea = { value: "" };
  const error = { textContent: "", hidden: true };
  const form = {
    addEventListener(name, listener) {
      listeners.set(name, listener);
    },
    querySelector(selector) {
      assert.equal(selector, "textarea[name='input']");
      return textarea;
    },
  };
  const document = {
    getElementById(id) {
      assert.equal(id, "request-error");
      return error;
    },
    querySelector(selector) {
      assert.equal(selector, "[data-agent-form]");
      return form;
    },
  };
  vm.runInNewContext(appScript, { document });

  return {
    form,
    textarea,
    error,
    dispatch(name, detail) {
      const event = { detail, stopped: false, stopPropagation() { this.stopped = true; } };
      listeners.get(name)(event);
      return event;
    },
  };
}

test("successful response clears the exact submitted draft", () => {
  const page = createFormPage();
  page.textarea.value = "  keep my spaces  ";

  page.dispatch("htmx:beforeRequest", { elt: page.form });
  page.dispatch("htmx:afterRequest", { elt: page.form, successful: true });

  assert.equal(page.textarea.value, "");
});

test("successful response keeps a newer draft", () => {
  const page = createFormPage();
  page.textarea.value = "first request";
  page.dispatch("htmx:beforeRequest", { elt: page.form });
  page.textarea.value = "new draft";

  page.dispatch("htmx:afterRequest", { elt: page.form, successful: true });

  assert.equal(page.textarea.value, "new draft");
});

test("HTTP, network, abort, and timeout failures preserve the draft", async (t) => {
  const cases = [
    ["HTTP failure", { successful: false, failed: true }],
    ["network failure", {}],
    ["abort", {}],
    ["timeout", {}],
  ];

  for (const [name, result] of cases) {
    await t.test(name, () => {
      const page = createFormPage();
      page.textarea.value = "keep this draft";
      page.dispatch("htmx:beforeRequest", { elt: page.form });
      page.dispatch("htmx:afterRequest", { elt: page.form, ...result });

      assert.equal(page.textarea.value, "keep this draft");
    });
  }
});

test("afterRequest without detail preserves the draft", () => {
  const page = createFormPage();
  page.textarea.value = "keep this draft";
  page.dispatch("htmx:beforeRequest", { elt: page.form });

  page.dispatch("htmx:afterRequest", undefined);

  assert.equal(page.textarea.value, "keep this draft");
});

test("successful events from another element do not clear the form", () => {
  const page = createFormPage();
  const otherElement = {};
  page.textarea.value = "keep this draft";

  page.dispatch("htmx:beforeRequest", { elt: page.form });
  page.dispatch("htmx:afterRequest", { elt: otherElement, successful: true });

  assert.equal(page.textarea.value, "keep this draft");
});

test("login page without the request form is harmless", () => {
  const document = {
    querySelector(selector) {
      assert.equal(selector, "[data-agent-form]");
      return null;
    },
  };

  assert.doesNotThrow(() => vm.runInNewContext(appScript, { document }));
});

test("JSON validation errors stay in the form and retain the draft", () => {
  const page = createFormPage();
  page.textarea.value = "keep this request";
  page.dispatch("htmx:beforeRequest", { elt: page.form });
  const event = page.dispatch("htmx:beforeOnLoad", {
    elt: page.form,
    xhr: { status: 400, responseText: '{"error":"input is required"}' },
  });
  page.dispatch("htmx:afterRequest", { elt: page.form, successful: false });

  assert.equal(event.stopped, true);
  assert.equal(page.error.textContent, "input is required");
  assert.equal(page.error.hidden, false);
  assert.equal(page.textarea.value, "keep this request");
});

test("network failures show an error and allow a retry", () => {
  const page = createFormPage();
  page.textarea.value = "keep this request";
  page.dispatch("htmx:beforeRequest", { elt: page.form });
  page.dispatch("htmx:afterRequest", { elt: page.form });

  assert.equal(page.error.hidden, false);
  assert.match(page.error.textContent, /did not finish/);
  assert.equal(page.textarea.value, "keep this request");
  page.dispatch("htmx:beforeRequest", { elt: page.form });
  assert.equal(page.error.hidden, true);
  assert.equal(page.error.textContent, "");
});

test("HTML failures and untrusted error text do not replace the document", () => {
  const page = createFormPage();
  page.dispatch("htmx:beforeOnLoad", {
    elt: page.form,
    xhr: { status: 500, responseText: '<script>bad()</script>' },
  });
  assert.match(page.error.textContent, /request failed/);
  page.dispatch("htmx:beforeOnLoad", {
    elt: page.form,
    xhr: { status: 400, responseText: JSON.stringify({error: '<script>bad()</script>'}) },
  });
  assert.equal(page.error.textContent, '<script>bad()</script>');
});
