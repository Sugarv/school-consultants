document.addEventListener('DOMContentLoaded', function() {
  var calendarEl = document.getElementById('calendar-metak');

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
          // info.el.style.borderColor = 'green';    // Optionally change the border color
        }
    }
  });

  calendar.render();
});