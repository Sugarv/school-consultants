jQuery(document).ready(function ($) {
  // Get references to the date1 and date2 input fields  
  const date1Field = document.querySelector('#id_date_from');
  const date2Field = document.querySelector('#id_date_to');

  // Date2 gets Date1's value
  if (date1Field && date2Field) {
    date1Field.addEventListener('focus', function () {
      date2Field.value = date1Field.value;
    });
  }

  
  // Handle financial fields
  const amount_per_km = 0.2
  const amount_away_per_day = 10

  // if pragmat is checked
  if ($('#id_pragmat').is(':checked')) {
    // check if km > 50
    if ($('#id_km').val() > 50 || $('#id_is_evaluation').prop('checked') == true){
      const amount_calc = ($('#id_km').val() * amount_per_km * 2).toPrecision(2);
      $('#id_to_pay').prop('checked', true);
      $('#id_to_pay').prop('disabled', false);
      $('#id_amount1').val(amount_calc);
      $('#id_away').prop('checked', true);
      $('#id_away').prop('disabled', false);
    } else {
      $('#id_amount1').val(0);
      $('#id_to_pay').prop('checked', false);
      $('#id_to_pay').prop('disabled', true);
      $('#id_amount2').val(0);
      $('#id_away').prop('checked', false);
      $('#id_away').prop('disabled', true);
    } 
  }

  // when pragmat changes
  $('#id_pragmat').change(() => {
    // pragmat -> true
    if ($('#id_pragmat').is(':checked')) {
      $('#id_to_pay').prop('disabled', false);
      // if km > 50
      if ($('#id_km').val() > 50 || $('#id_is_evaluation').prop('checked') == true){
        $('#id_to_pay').prop('checked', true);
        $('#id_away').prop('checked', true);
        $('#id_away').prop('disabled', false);
        const amount_calc = ($('#id_km').val() * amount_per_km * 2).toPrecision(2);
        $('#id_amount1').val(amount_calc);
        $('#id_amount2').val(amount_away_per_day);
      }
      $('#id_to_pay').prop('disabled', true);
      $('#id_away').prop('disabled', true);
      $('#id_amount1').prop('disabled', false);
    } else {
      $('#id_to_pay').prop('disabled', true);
      $('#id_amount1').prop('disabled', true);
      $('#id_to_pay').prop('checked', false);
      $('#id_away').prop('checked', false);
      $('#id_away').prop('disabled', true);
      $('#id_amount1').val(0.0);
      $('#id_amount2').val(0.0);

    }
  });

  // when km changes
  $('#id_km').change(() => {
    if ($('#id_km').val() > 50 || $('#id_is_evaluation').prop('checked') == true){
      const amount1 = ($('#id_km').val() * amount_per_km * 2).toPrecision(2);
      $('#id_to_pay').prop('checked', true);
      $('#id_to_pay').prop('disabled', false);
      $('#id_amount1').val(amount1);
      $('#id_away').prop('checked', true);
      $('#id_away').prop('disabled', false);
      $('#id_amount2').val(amount_away_per_day);
    } else {
      $('#id_amount1').val(0);
      $('#id_to_pay').prop('checked', false);
      $('#id_to_pay').prop('disabled', true);
      $('#id_away').prop('checked', false);
      $('#id_away').prop('disabled', true);
      $('#id_amount2').val(0.0);
    }
  });

  // when 'to_pay' changes
  $('#id_to_pay').change(() => {    
    if ($('#id_to_pay').prop('checked', false)){
      $('#id_amount1').val(0.0);
      // $('#id_amount1').prop('disabled', true);
    }
  });
  // when 'away' changes
  $('#id_away').change(() => {    
    if ($('#id_away').prop('checked', false)){
      $('#id_amount2').val(0.0);
      // $('#id_amount1').prop('disabled', true);
    }
  });

  // when 'is_evaluation' changes
  $('#id_is_evaluation').change(() => {    
    if ($('#id_is_evaluation').prop('checked') == false && $('#id_km').val() < 50){
      $('#id_to_pay').prop('checked', false);
      $('#id_amount1').val(0.0);
      $('#id_away').prop('checked', false);
      $('#id_amount2').val(0.0);
      // $('#id_amount1').prop('disabled', true);
    } else {
      $('#id_to_pay').prop('checked', true);
      const amount1 = ($('#id_km').val() * amount_per_km * 2).toPrecision(2);
      $('#id_amount1').val(amount1);
      $('#id_away').prop('checked', true);
      $('#id_amount2').val(amount_away_per_day);
    }
  });

});
