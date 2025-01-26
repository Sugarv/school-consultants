$(document).ready(function() {
  $('.multidatepicker').each(function() {
      var $this = $(this);
      var existingDates = $this.val();

      // Parse existing dates if available
      if (existingDates) {
          try {
              existingDates = JSON.parse(existingDates);
          } catch (e) {
              console.error("Error parsing existing dates:", e);
              existingDates = [];
          }
      } else {
          existingDates = [];
      }

      // Initialize the multiDatesPicker
      $this.multiDatesPicker({
          dateFormat: "yy-mm-dd",
          addDates: existingDates,
          onSelect: function(dateText) {
            console.log((dateText));
              // Get the current dates from the input field
              var currentDates = existingDates;
              
              // Add the newly selected date
              currentDates.push(dateText);
              
              // Remove duplicates
              currentDates = [...new Set(currentDates)];
              
              // Update the input field with the new list of dates
              $this.val(JSON.stringify(currentDates));
          }
      });

      // Ensure the input field is always a valid JSON array
      $this.on('change', function() {
        console.log('change');
          try {
              var value = $this.val();
              if (value) {
                  JSON.parse(value); // Validate JSON
              } else {
                  $this.val('[]'); // Set to empty array if empty
              }
          } catch (e) {
              console.error("Invalid JSON detected, resetting to empty array.");
              $this.val('[]');
          }
      });
  });
}); 