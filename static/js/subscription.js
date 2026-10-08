const planButtons =
    document.querySelectorAll(".choose-plan");


planButtons.forEach((button) => {

    button.addEventListener(
        "click",
        function () {

            const selectedPlan =
                button.dataset.plan;

            if (!selectedPlan) {
                alert("Please select a valid plan.");
                return;
            }

            window.location.href =
                `/payment?plan=${encodeURIComponent(selectedPlan)}`;
        }
    );

});