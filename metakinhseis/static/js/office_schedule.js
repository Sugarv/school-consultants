$(document).ready(function() {
    var $hiddenInput = $('#id_days_in_office'); // The hidden input field
    var existingDates = $hiddenInput.val(); // Read initial value from the hidden input field

    // Safely parse existing dates if available, or initialize as an empty array
    try {
        existingDates = existingDates ? JSON.parse(existingDates) : [];
    } catch (e) {
        console.error("Error parsing existing dates:", e);
        existingDates = [];
    }

    // console.log("Existing Dates:", existingDates);
    // Disable days_in_office field
    $('#id_days_in_office').prop('readonly', true);
    $('#id_days_in_office').hide();

    // Initialize the MultiDatesPicker
    var $picker = $('#multidatepicker-div').multiDatesPicker({
        dateFormat: "yy-mm-dd",
        onSelect: function (dateText) {
            // Get the current dates from the hidden input field
            var currentDates = JSON.parse($hiddenInput.val() || '[]');

            // Check if the selected date already exists in the array
            var index = currentDates.indexOf(dateText.trim());

            if (index > -1) {
                // If the date exists, remove it (toggle behavior)
                currentDates.splice(index, 1);
            } else {
                // If not, add the date
                currentDates.push(dateText.trim());
            }

            // Sort dates for consistency
            currentDates.sort();

            // console.log("Updated Dates:", currentDates);

            // Update the hidden input field with the new list of dates
            $hiddenInput.val(JSON.stringify(currentDates));
        }
    });

    // Ensure dates are highlighted when loading
    if (existingDates.length > 0) {
        $picker.multiDatesPicker('addDates', existingDates);
    }

    // Ensure the hidden input starts with valid JSON
    $hiddenInput.val(JSON.stringify(existingDates));
});