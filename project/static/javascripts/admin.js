$(document).ready (function() {
  $('#js-submit-data').click(function(event){
    event.preventDefault();

    let teamData = {};
    $('#bracket').find('input').each(function() {
      const seedID = $(this).attr('data-seed-id');
      const gameID = $(this).attr('data-game-id');
      const teamName = $(this).val();

      teamData[teamName] = {seedID: seedID, gameID: gameID};
    });

    $.ajax({
      type: 'POST',
      url: window.location.pathname,
      data: {teamData: JSON.stringify(teamData)},
      success: function (result) {
        // check for errors better
        alert('All good');
      }
    });
  });
});