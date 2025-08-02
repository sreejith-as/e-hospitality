document.addEventListener('DOMContentLoaded', function () {
  const departmentSelect = document.getElementById('id_department');
  const doctorSelect = document.getElementById('id_doctor');
  const dateInput = document.getElementById('id_date');
  const timeInput = document.getElementById('id_time');

  function clearSelectOptions(selectElement) {
    selectElement.innerHTML = '<option value="" disabled selected>Choose Doctor</option>';
  }

  function fetchDoctors(departmentId) {
    if (!departmentId) {
      clearSelectOptions(doctorSelect);
      return;
    }
    fetch(`/patients/get_doctors_by_department/?department_id=${departmentId}`)
      .then(response => response.json())
      .then(data => {
        clearSelectOptions(doctorSelect);
        data.doctors.forEach(doctor => {
          const option = document.createElement('option');
          option.value = doctor.id;
          option.textContent = doctor.username;
          doctorSelect.appendChild(option);
        });
      });
  }

  function fetchAvailableSlots(doctorId, date) {
    if (!doctorId || !date) {
      timeInput.value = '';
      timeInput.disabled = true;
      return;
    }
    fetch(`/patients/get_available_time_slots/?doctor_id=${doctorId}&date=${date}`)
      .then(response => response.json())
      .then(data => {
        if (data.available_slots && data.available_slots.length > 0) {
          timeInput.disabled = false;
          // Create a datalist for time input suggestions
          let datalist = document.getElementById('time_slots');
          if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.id = 'time_slots';
            timeInput.setAttribute('list', 'time_slots');
            timeInput.parentNode.appendChild(datalist);
          }
          datalist.innerHTML = '';
          data.available_slots.forEach(slot => {
            const option = document.createElement('option');
            option.value = slot;
            datalist.appendChild(option);
          });
        } else {
          timeInput.value = '';
          timeInput.disabled = true;
          if (datalist) {
            datalist.innerHTML = '';
          }
        }
      });
  }

  departmentSelect.addEventListener('change', function () {
    fetchDoctors(this.value);
    // Clear time input when department changes
    timeInput.value = '';
    timeInput.disabled = true;
  });

  doctorSelect.addEventListener('change', function () {
    fetchAvailableSlots(this.value, dateInput.value);
  });

  dateInput.addEventListener('change', function () {
    fetchAvailableSlots(doctorSelect.value, this.value);
  });

  // Initialize time input as disabled
  timeInput.disabled = true;
});
