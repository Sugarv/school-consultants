document.addEventListener('DOMContentLoaded', function() {
  var calendarEl = document.getElementById('calendar-metak');

  var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      events: '/metakinhsh-json/',  // The URL from step 2
      locale: 'el', // Set the locale for Greek
      eventDidMount: function (info) {
        // source: https://fullcalendar.io/docs/event-tooltip-demo
        var tooltip = new Tooltip(info.el, {
          title: info.event.extendedProps.description,
          placement: 'top',
          trigger: 'hover',
          // container: 'body'
        });
        // Check if the event is marked as complete and change its color
        if (info.event.extendedProps.egkrish) {
          info.el.style.backgroundColor = 'green'; // Change the event background color
          info.el.style.borderColor = 'green';    // Optionally change the border color
        }
    }
  });

  calendar.render();
});