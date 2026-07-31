(() => {
  const form = document.getElementById("loginForm");
  const email = document.getElementById("email");
  const password = document.getElementById("password");
  const emailError = document.getElementById("emailError");
  const passwordError = document.getElementById("passwordError");
  const toggle = document.getElementById("togglePassword");

  toggle?.addEventListener("click", () => {
    const show = password.type === "password";
    password.type = show ? "text" : "password";
    toggle.textContent = show ? "Hide" : "Show";
    toggle.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });

  form?.addEventListener("submit", event => {
    let valid = true;
    if (!email?.checkValidity()) {
      valid = false;
      if (emailError) emailError.textContent = "Enter a valid email address.";
      email?.classList.add("invalid");
    } else {
      if (emailError) emailError.textContent = "";
      email?.classList.remove("invalid");
    }
    if (!password?.value || password.value.length !== 10) {
      valid = false;
      if (passwordError) passwordError.textContent = "Password must be exactly 10 characters.";
      password?.classList.add("invalid");
    } else {
      if (passwordError) passwordError.textContent = "";
      password?.classList.remove("invalid");
    }
    if (!valid) event.preventDefault();
  });
})();
