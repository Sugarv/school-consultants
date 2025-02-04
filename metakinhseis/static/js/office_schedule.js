// Uses MultiDatesPicker for jQuery UI
// http://luca.lauretta.info/Multiple-Dates-Picker-for-jQuery-UI/

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

  // Disable days_in_office field
  $('#id_days_in_office').prop('readonly', true);
  $('#id_days_in_office').hide();

  // Function to disable weekends (Saturday & Sunday)
  function disableWeekends(date) {
      var day = date.getDay();
      return [(day !== 0 && day !== 6)]; // 0 = Sunday, 6 = Saturday
  }

  // Initialize the MultiDatesPicker
  var $picker = $('#multidatepicker-div').multiDatesPicker({
      dateFormat: "yy-mm-dd",
      beforeShowDay: disableWeekends, // Disable weekends
      onSelect: function(dateText) {
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

          // Update the hidden input field with the new list of dates
          $hiddenInput.val(JSON.stringify(currentDates));
      }
  });

  // Ensure dates are highlighted when loading
  if (existingDates.length > 0) {
      $picker.multiDatesPicker('addDates', existingDates);

      // Set the displayed month to the month of the first existing date
      var firstDate = $.datepicker.parseDate("yy-mm-dd", existingDates[0]);
      $('#multidatepicker-div').datepicker("setDate", firstDate);
  }

  // Ensure the hidden input starts with valid JSON
  $hiddenInput.val(JSON.stringify(existingDates));
});
