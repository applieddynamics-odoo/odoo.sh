/** @odoo-module **/

document.addEventListener("click", function (ev) {

    /* ---------------------------------------------------------
       Problem statement toggle
       --------------------------------------------------------- */

    const button = ev.target.closest(".adi_problem_toggle");

    if (button) {
        ev.preventDefault();

        const card = button.closest(".adi_subject_card");
        const problem = card && card.querySelector(".adi_problem_inline");

        if (!problem) {
            return;
        }

        const expanded = problem.classList.toggle("adi_problem_expanded");
        const icon = button.querySelector("i");

        if (icon) {
            if (expanded) {
                icon.classList.remove("fa-plus-square");
                icon.classList.add("fa-minus-square");
                button.title = "Collapse";
            } else {
                icon.classList.remove("fa-minus-square");
                icon.classList.add("fa-plus-square");
                button.title = "Expand";
            }
        } else {
            button.textContent = expanded ? "Show less" : "Show more";
        }
    }

    /* ---------------------------------------------------------
       Management notes toggle
       --------------------------------------------------------- */

    const notesButton = ev.target.closest(".adi_management_notes_toggle");

    if (notesButton) {
        ev.preventDefault();

        const card = notesButton.closest(".adi_management_card");
        const notes = card && card.querySelector(".adi_management_notes_inline");

        if (!notes) {
            return;
        }

        const expanded = notes.classList.toggle("adi_management_notes_expanded");
        const icon = notesButton.querySelector("i");

        if (icon) {
            if (expanded) {
                icon.classList.remove("fa-plus-square");
                icon.classList.add("fa-minus-square");
                notesButton.title = "Collapse";
            } else {
                icon.classList.remove("fa-minus-square");
                icon.classList.add("fa-plus-square");
                notesButton.title = "Expand";
            }
        }
    }

});