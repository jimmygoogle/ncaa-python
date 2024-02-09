function validateForm() {
  let status = true;
  const $contactForm = $('#contact');
  const name = $contactForm.find('#name').val();
  const emailAddress = $contactForm.find('#email_address').val();
  const message = $contactForm.find('#message').val();

  let error_message;
  // get rid of error messages once the pool is submitted
  $("#error").empty();

  if(status && !name) {
    error_message = 'Oops, it looks like you forgot to enter your name.';
    $contactForm.find('#username').focus();
    status = false;
  }

  if(status && !emailAddress || status && !emailAddress.match(/\@/)) {
    error_message = 'Oops, it looks like you forgot to enter a valid email address for us to contact you at.';
    $contactForm.find('#email_address').focus();
    status = false;
  }

  if(status && !message) {
    error_message = 'Please enter a cool message for us to read.';
    $contactForm.find('#message').focus();
    status = false;
  }

  // show error message
  if(error_message) {
    $("#error")
    .empty()
    .append(error_message);
    return false;
  }

  return status;
}