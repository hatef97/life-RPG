document.addEventListener("DOMContentLoaded", () => {
    const navToggle = document.querySelector("[data-nav-toggle]");
    if (navToggle) {
        navToggle.addEventListener("click", () => {
            document.body.classList.toggle("nav-open");
        });
    }

    document.querySelectorAll(".main-nav a").forEach((link) => {
        link.addEventListener("click", () => document.body.classList.remove("nav-open"));
    });

    document.querySelectorAll("[data-message-close]").forEach((button) => {
        button.addEventListener("click", () => {
            button.closest(".message")?.remove();
        });
    });

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
