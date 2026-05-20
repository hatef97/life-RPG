document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;

    // All elements that open the sidebar (topbar hamburger + bottom-nav More button)
    document.querySelectorAll("[data-nav-toggle]").forEach((btn) => {
        btn.addEventListener("click", () => body.classList.toggle("nav-open"));
    });

    // Click overlay to close sidebar
    const overlay = document.querySelector("[data-nav-overlay]");
    if (overlay) {
        overlay.addEventListener("click", () => body.classList.remove("nav-open"));
    }

    // Close sidebar when any nav link is clicked
    document.querySelectorAll(".main-nav a, .bottom-nav a").forEach((link) => {
        link.addEventListener("click", () => body.classList.remove("nav-open"));
    });

    // Dismiss toast messages
    document.querySelectorAll("[data-message-close]").forEach((button) => {
        button.addEventListener("click", () => button.closest(".message")?.remove());
    });

    // Sync range inputs with their output labels
    document.querySelectorAll(".range-input").forEach((input) => {
        const output = input.parentElement?.querySelector("output");
        if (!output) return;
        const sync = () => {
            output.value = input.value;
            output.textContent = input.value;
        };
        input.addEventListener("input", sync);
        sync();
    });
});
