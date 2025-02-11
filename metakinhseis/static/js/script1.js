document.addEventListener('DOMContentLoaded', function() {
  var calendarEl = document.getElementById('calendar-metak');
  var showOfficeDays = true; // Initial state

  var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      headerToolbar: {
        left: 'prev,next today', // Navigation buttons
        center: 'title', // Calendar title
        right: 'dayGridMonth,timeGridWeek,timeGridDay' // Buttons for Month, Week, Day
      },
      events: '/metakinhsh-json/',  // The URL from step 2
      locale: 'el', // Set the locale for Greek
      views: {
        timeGridWeek: {
            allDaySlot: true, // Ensure the all-day slot is visible
            slotMinTime: "00:00:00", // Start time
            slotMaxTime: "00:00:00", // Hide the hourly slots (alternative: use CSS)
        }
      },
      eventDidMount: function (info) {
        // source: https://fullcalendar.io/docs/event-tooltip-demo
        var tooltip = new Tooltip(info.el, {
          title: info.event.extendedProps.description,
          placement: 'bottom',
          trigger: 'hover',
          // container: 'body'
        });
        // Check if the event is marked as complete and change its color
        if (info.event.extendedProps.egkrish) {
          info.el.style.backgroundColor = 'green'; // Change the event background color
          info.el.style.borderColor = 'green';    // Optionally change the border color
        }
        if (info.event.extendedProps.officeDay) {
          info.el.style.backgroundColor = 'brown'; // Change the event background color
          if (!showOfficeDays) {
            info.el.style.display = 'none';
          }
        }
    }
  });

  calendar.render();

  // Add event listener for the toggle button
  const toggleButton = document.getElementsByName('toggleOfficeDays')[0]; // Get first element
  if (toggleButton) {
    // Set initial button text
    toggleButton.textContent = showOfficeDays ? 'Απόκρυψη Ημ.Γραφείου' : 'Εμφάνιση Ημ.Γραφείου';
    
    toggleButton.addEventListener('click', function() {
      showOfficeDays = !showOfficeDays;
      // Update button text
      toggleButton.textContent = showOfficeDays ? 'Απόκρυψη Ημ.Γραφείου' : 'Εμφάνιση Ημ.Γραφείου';
      // Refresh all events
      calendar.refetchEvents();
    });
  }
});