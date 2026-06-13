// main.js — students will add JavaScript here as features are built

document.addEventListener("DOMContentLoaded", function() {
    const customToggle = document.getElementById("custom-filter-toggle");
    const customForm = document.getElementById("custom-date-form");
    if (customToggle && customForm) {
        customToggle.addEventListener("click", function() {
            customForm.classList.toggle("hidden");
            if (!customForm.classList.contains("hidden")) {
                const startDateField = document.getElementById("start_date");
                if (startDateField) {
                    startDateField.focus();
                }
            }
        });
    }
});
