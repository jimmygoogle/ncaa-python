let userPicks = {};

$(document).ready (
  function() {

    // load the 'userPicks' object
    loadUserPicks();
    
    // control bracket flow
    $('li').click(function() {
      setUserPick($(this));
    });

    // submit form to set/check user pool name
    $("#poolNameForm").submit( function(event) {
      event.preventDefault();
      checkUserPool();
    });
  }
);

function loadUserPicks() {
  const $userBracketInfoForm = $('#userBracketInfoForm');
  const bracketType = $userBracketInfoForm.find('#bracketType').val();
  const editTypeValue = $userBracketInfoForm.find('#editType').val();
  
  if(editTypeValue == 'admin' || editTypeValue == 'add') {
    return false;
  }

  $('#bracket').find('li').each(function() {      
    const slotData = $(this).attr('id').match(/slot(\d+)/);
    const startSlot = (bracketType == 'sweetSixteenBracket') ? 113 : 65;
  
    if(slotData[1] >= startSlot) {
      const teamID = $(this).attr('data-team-id');
      const gameID = slotData[1] - 64
      if(teamID > 0) {
        userPicks[gameID] = teamID;
      }        
    }
  });

  const winnerTeamID = $('#ncaaWinner').attr('data-team-id');
  if(winnerTeamID > 0) {
    userPicks[63] = winnerTeamID;
  }
  //console.log(userPicks);
}

function checkUserPool() {
  $.ajax({
  type: "POST",
  url:  "/pool",
  data: {
    'dataPosted': 1,
    'poolName': $("input#userPoolName").val()
  },
  success: function(result) {
    //pool finder failed
    if(result.status == 0) {
      $("#userPoolMessage").empty().show().append('*Please check your pool name.');
    }
    //we found a pool name
    else {
      window.location = '/';
    }
  }
  });
}

function validateUserInput() {
  let status = true;
  let multipleEdits = false;
  const $userBracketInfoForm = $('#userBracketInfoForm');
  const editTypeValue = $userBracketInfoForm.find('#editType').val();
  const bracketTypeName = $userBracketInfoForm.find('#bracketType').val();
  const emailAddress = $userBracketInfoForm.find('#email').val();
  const username = $userBracketInfoForm.find('#username').val();
  const firstName = $userBracketInfoForm.find('#firstname').val();
  const tieBreakerPoints = $userBracketInfoForm.find('#tieBreaker').val();

  if( (editTypeValue == 'admin') || (editTypeValue == 'edit')) {
    multipleEdits = true;
  }

  let error_message;
  // get rid of error messages once the pool is submitted
  $("#error").empty();

  if(editTypeValue !== 'admin') {
    // the expected number of user picks changes based on the bracket type
    const expectedNumberOfGames = (bracketTypeName == 'sweetSixteenBracket') ? 15 : 63;

    //make sure all games are filled in when we are filling out a bracket
    if(Object.keys(userPicks).length !== expectedNumberOfGames && (editTypeValue == 'add')) {
      error_message = 'Please pick all of the games.';
      status = false;
    }
    
    // if we are editing a user changes their pick we are clear that team from other fields
    // make sure they filled those in again
    if((editTypeValue == 'edit')) {
      $('#bracket').find('li').each(function() {
        if(!$(this).attr('data-team-id')) {
          error_message = 'Please pick all of the games.';
          status = false;
        }
      });
    }

    if(status && !emailAddress || status && !emailAddress.match(/\@/)) {
      error_message = 'A valid email address is required.';
      $userBracketInfoForm.find('#email').focus();
      status = false;
    }

    if(status && !username) {
      error_message = 'A bracket name is required.';
      $userBracketInfoForm.find('#username').focus();
      status = false;
    }

    if(status && (!tieBreakerPoints || isNaN(tieBreakerPoints))) {
      error_message = 'Tie breaker points are required.';
      $userBracketInfoForm.find('#tieBreaker').focus();
      status = false;
    }

    if(status && !tieBreakerPoints.match(/\b[0-9]{1,3}\b/)) {
      error_message = 'Please enter a valid guess for your total points.';
      $userBracketInfoForm.find('#tieBreaker').focus();
      status = false;
    }
  }

  // show error message
  if(error_message) {
    $("#error")
    .empty()
    .append(error_message);
  }

  if(status) {
    // set base data
    const data = {
      emailAddress: emailAddress,
      username: username,
      firstName: firstName,
      tieBreakerPoints: tieBreakerPoints,
      bracketTypeName: bracketTypeName,
      userPicks: JSON.stringify(userPicks)
    };

    $.ajax({
      type: 'POST',
      url: window.location.pathname,
      data: data,
      success: function (result) {
        //disable submit button so the users do not flood the system
        $("#submit").hide();

        // fade slowly when you are not allowing the user to edit multiple times
        const fadeInterval = multipleEdits ? 2000 : 4000;
        const msg = multipleEdits ? 'Your bracket has been updated.' : 'Your bracket has been submitted. <br/> Good luck!';

        $("#message")
        .empty()
        .show()
        .append(msg)
        .fadeOut(fadeInterval, function(){
          // allow multiple edits
          if( multipleEdits ) {
            $("#submit").show();
          }
        });
      }
    });

  }

  return(false);
}

function setUserPick(obj) {
  // set team user picked ex: 5 Utah
  const userPickedTeam = obj.text();

  // get game number and all possible game slots that the user pick could play in
  // ex: class = "matchup game1 65|97|113|121|125" (we need the 2nd and 3rd element)
  const gameData = obj.parent().attr('class').split(' ');

  const gameSlots = obj.parent().attr('data-games');
  const teamID = obj.attr('data-team-id');

  //we want to not allow the user to edit any games previous played if we are in the sweet 16
  const game = gameData[1].match(/game(\d+)/);

  if((game[1] < 49) && $('#bracketType').val() == 'sweetSixteenBracket') {
    return;
  }

  // clear all previous picks (in case user is changing pick)
  clearPreviousPicks(gameData[1], userPickedTeam, gameSlots);

  // set data so it can be submitted to DB
  setUserFormData(gameData[1], teamID);

  // slot data looks like 81|105|119|127
  if(gameSlots) {
    let slotData = gameSlots.split('|');

    // get and set next game slot
    const newSlot = slotData.shift();

    // this is the final game winner
    if(newSlot === 'none') {
      $('#slot125').removeClass('winner');
      $('#slot126').removeClass('winner');
      obj.addClass('winner');
      userPicks[63] = teamID;
    }
    else {
      // set new pick
      const $slot = $('#slot' + newSlot);
      $slot.attr('data-team-id', teamID);
      $slot.empty().append(userPickedTeam);
    }
  }
  //console.log(userPicks);
}

function setUserFormData(gameData, teamID) {
  const gameID = parseInt(gameData.match(/\d+/));
  userPicks[gameID] = teamID;
}

function clearPreviousPicks(gameNumber, userPickedTeam, slotString) {
  //get the 'other' team in the current game the user is picking
  const getOtherTeamInGame = _getOtherTeamInGame(gameNumber, userPickedTeam);
  //console.log('other team in game is ' + getOtherTeamInGame);

  if(getOtherTeamInGame){
    // only check (match) specified slots (ex 81|105|119|127)
    const slotMatch = eval('/' + slotString + '/');

    //check the rest of the bracket now for the existence of the 'other team' and remove it
    //this is needed for when the user changes their pick(s)
    $('#bracket').find('li').each(function() {
      // we only need to check games from round #2 on
      // it starts at 'slot65' (string to be parsed)
      const slotNumber = parseInt( $(this).attr('id').match(/\d+/) );

      // start at slot 65 and only clear potential games (we dont want to clear all games)
      if(
        (slotNumber >= 65)
        &&
        (slotMatch.test(slotNumber) )
      ){
        const pick = $(this).text();

        //get rid of all future picks that match
        if(pick.match(getOtherTeamInGame) ){
          $(this).empty();
          $(this).attr('data-team-id', '');
        }
      }
    });
  }
}

function _getOtherTeamInGame(gameNumber, userPickedTeam) {
  let teamsInGame = [];

  //get both teams in game
  $( '.' + gameNumber).find('li').each(function() {
    //clean string and put into array
    teamsInGame.push( $.trim( $(this).text() ) );
  });

  let arrayIndex = $.inArray(userPickedTeam, teamsInGame);

  if(arrayIndex == 0) {
    arrayIndex++;
  }
  else {
    arrayIndex--;
  }

  return(teamsInGame[ arrayIndex ]);
}
