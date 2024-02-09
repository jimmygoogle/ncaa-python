$(window).on('load', function() {
  // submit form to set/check user pool name
  $('#poolNameForm').submit(function(event) {
    event.preventDefault();
    checkUserPool();
  });
 });

 function checkUserPool() {
  $.post(
    "/pool",
    {
      'dataPosted': 1,
      'poolName': $("input#userPoolName").val().toLowerCase()
    },
    function(result) {
      //pool finder failed
      if(result == 0) {
        $("#userPoolMessage").empty().show().addClass('user_pool_message_background').append('* Please check your pool name.');
      }
      //we found a pool name
      else {
        window.location = '/';
      }
    }
  );
}
