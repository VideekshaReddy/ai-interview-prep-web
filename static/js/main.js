
document.addEventListener("DOMContentLoaded", function () {

    // Highlight the current page in the navbar
    const currentPath = window.location.pathname;

    const navLinks = document.querySelectorAll(".nav-links a");

    navLinks.forEach(function (link) {
        const linkPath = new URL(link.href).pathname;

        if (linkPath === currentPath) {
            link.classList.add("active");
        }
    });


    // Basic form validation
    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener("submit", function (event) {

            const requiredFields = form.querySelectorAll("[required]");
            let isValid = true;

            requiredFields.forEach(function (field) {

                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = "#e74c3c";
                } else {
                    field.style.borderColor = "#ddd";
                }

            });

            if (!isValid) {
                event.preventDefault();
                alert("Please fill in all required fields.");
            }

        });

    });


    // Smooth scrolling for internal section links
    const sectionLinks = document.querySelectorAll('a[href^="#"]');

    sectionLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            const target = document.querySelector(link.getAttribute("href"));

            if (target) {
                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth"
                });
            }

        });

    });

});
