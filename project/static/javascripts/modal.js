$(document).ready (function() {
  const modal = document.getElementById("modal");

  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  }

  // show modal only once
  let cookie = document.cookie;

  if(!cookie.match(/modal/)) {
    modal.style.display = "block";
    document.cookie = "modal=1";
  }
});
