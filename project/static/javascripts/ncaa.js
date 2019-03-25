let userPicks = {};

$(document).ready (
  function() {

    // load the 'userPicks' object
    loadUserPicks();
    
    $('.picks-header').click(function(){
      $('.auto-picks-buttons').toggle();
    });
    
    // control bracket flow
    $('li').click(function() {
      setUserPick($(this));
    });

    $('#reset').click(function(event){
      event.preventDefault();
      resetPicks();
    });

    $('#chalk').click(function(event){
      event.preventDefault();
      makePicks('chalk');
    });

    $('#mix').click(function(event){
      makePicks('mix');
    });

    $('#random').click(function(event){
      makePicks('random');
    });
    // submit form to set/check user pool name
    $('#poolNameForm').submit(function(event) {
      event.preventDefault();
      checkUserPool();
    });
    
    // validate and submit user bracket form
    $('#submit_user_bracket').click(function(event) {
      event.preventDefault();
      validateUserInput();
    });
  }
);

function resetPicks() {

  // loop through all games and reset picks
  for (let index = 33; index <= 63; index++) {

    $('.game' + index).find('li').each(function(){
      $(this).empty();
      $(this).attr('data-team-id', '');
    });
  }

  userPicks = {};
}

function makePicks(type) {
  let game = '';
  let games = [];
  
  // added some weighting for seeds by round
  // https://www.betfirm.com/seeds-national-championship-odds/
  const weights = {
    1 : {
      1 : 0.999999,    
      2 : 0.939,
      3 : 0.841,
      4 : 0.803,
      5 : 0.644,
      6 : 0.629,
      7 : 0.614,
      8 : 0.508,
      9 : 0.492,
      10 : 0.386,
      11 : 0.371,
      12 : 0.356,
      13 : 0.197,
      14 : 0.159,
      15 : 0.061,
      16 : 0.000001
    },
    2 : {
      1 : 0.864,
      2 : 0.629,
      3 : 0.508,
      4 : 0.47,
      5 : 0.326,
      6 : 0.326,
      7 : 0.189,
      8 : 0.098,
      9 : 0.038,
      10 : 0.182,
      11 : 0.152,
      12 : 0.152,
      13 : 0.045,
      14 : 0.015,
      15 : 0.008,
      16 : 0.0
    },
    3 : {
      1 : 0.697,
      2 : 0.462,
      3 : 0.242,
      4 : 0.159,
      5 : 0.061,
      6 : 0.106,
      7 : 0.076,
      8 : 0.061,
      9 : 0.015,
      10 : 0.061,
      11 : 0.053,
      12 : 0.008,
      13 : 0.0,
      14 : 0.0,
      15 : 0.0,
      16 : 0.0
    },
    4 : {
      1 : 0.409,
      2 : 0.212,
      3 : 0.114,
      4 : 0.098,
      5 : 0.045,
      6 : 0.023,
      7 : 0.023,
      8 : 0.38,
      9 : 0.008,
      10 : 0.008,
      11 : 0.023,
      12 : 0.0,
      13 : 0.0,
      14 : 0.0,
      15 : 0.0,
      16 : 0.0
    },
    5 : {
      1 : 0.242,
      2 : 0.098,
      3 : 0.068,
      4 : 0.023,
      5 : 0.023,
      6 : 0.015,
      7 : 0.015,
      8 : 0.023,
      9 : 0.0,
      10 : 0.0,
      11 : 0.0,
      12 : 0.0,
      13 : 0.0,
      14 : 0.0,
      15 : 0.0,
      16 : 0.0
    },
    6 : {
      1 : 0.152,
      2 : 0.038,
      3 : 0.03,
      4 : 0.008,
      5 : 0.088,
      6 : 0.008,
      7 : 0.008,
      8 : 0.008,
      9 : 0.0,
      10 : 0.0,
      11 : 0.0,
      12 : 0.0,
      13 : 0.0,
      14 : 0.0,
      15 : 0.0,
      16 : 0.0
    }
  };
  
  // loop through all games and make picks based on user preference
  for (let index = 1; index <= 63; index++) {
    
    teams = []
    $('.game' + index).find('li').each(function(){
      // get seed and team ... ex: 1 Virginia
      const teamInfo = $(this).html().trim().split(' ');
      const seedId = teamInfo[0]; 

      if(!seedId) {
        return true;
      }

      // get game and round
      const gameData = $(this).parent().attr('class').split(' ');
      const game = gameData[1].match(/game(\d+)/);
      const round = getRound(game[1]);
      
      const data = {seed_id: seedId, round: round, game: $(this)};
      teams.push(data);
    });
    
    if(teams.length) {
      // sort based on seed (chalk, weighted, random)
      teams.sort(function(a, b){
        
        switch(type) {
          case 'random':
            return 0.5 - Math.random();
          case 'chalk':
            // if the seeds equal pick a random one since we dont know the teams
            if(a.seed_id == b.seed_id) {
              return 0.5 - Math.random();
            }
            else{
              return a.seed_id - b.seed_id;
            }
          case 'mix':
            // if the seeds equal pick a random one since we dont know the teams
            if(a.seed_id == b.seed_id) {
              return 0.5 - Math.random();
            }
            // make a pick based on weight
            // this logic might need to be reworked with a better method
            else {
              let data = {};
              data[a.seed_id] = weights[a.round][a.seed_id];
              data[b.seed_id] = weights[b.round][b.seed_id];

              // figure out the seed with better probability
              if(weights[a.round][a.seed_id] < weights[b.round][b.seed_id]) {
                higher_probability_seed = b.seed_id;
                lower_probability_seed = a.seed_id;
              }
              else {
                higher_probability_seed = a.seed_id;
                lower_probability_seed = b.seed_id;
              }

              // generate random number
              random_number = generateRandomNumber(data);
              
              // if the random number is less than or equal to the lower probability seed return that one
              if(parseFloat(random_number) <= parseFloat(data[ lower_probability_seed ])) {
                return b.seed_id - a.seed_id;
              }
              // return the higher seed
              else {
                return a.seed_id - b.seed_id;
              }
            }
        }
      });

      // set pick
      teams[0].game.trigger('click');
    }    
  }
}

customSort = function(a,b) {
  return [a.a, a.b] > [b.a, b.b] ? 1:-1;
}

function getRound(game) {
  let round = 0;

  if(game <= 32) {
    round = 1;
  }
  else if(game >= 33 && game <= 48) {
    round = 2;
  }
  else if(game >= 49 && game <= 56) {
    round = 3;
  }
  else if(game >= 57 && game <= 60) {
    round = 4;
  }
  else if(game == 61 || game == 62) {
    round = 5;
  }
  else {
    round = 6;
  }

  return round;
}

function generateRandomNumber(data) {
  let index;
  let sum = 0; 

  // determine max
  const min = 0;
  let max = 0;
  for (index in data) {
    max += data[index];
  }

  // generate random number between min and max
  return (Math.random() * (max - min) + min).toFixed(3);
}
    
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
    'poolName': $("input#userPoolName").val().toLowerCase()
  },
  success: function(result) {
    //pool finder failed
    if(result == 0) {
      $("#userPoolMessage").empty().show().addClass('user_pool_message_background').append('*Please check your pool name.');
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
  const tieBreakerPoints = parseInt($userBracketInfoForm.find('#tieBreaker').val());

  let formAction = 'POST';
  
  // this is kind a hack for the bracket route
  const rand_string = Math.random().toString(36).substring(7);
  let url = window.location.href + 'bracket/' + rand_string;

  if( (editTypeValue == 'admin') || (editTypeValue == 'edit')) {
    multipleEdits = true;
    formAction = 'PUT';
    url = window.location.href;
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

    if(status && (tieBreakerPoints < 100 || tieBreakerPoints > 200)) {
      error_message = 'Please enter a valid guess<br>for your total points.';
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
      email_address: emailAddress,
      username: username,
      first_name: firstName,
      tie_breaker_points: tieBreakerPoints,
      bracket_type_name: bracketTypeName,
      user_picks: JSON.stringify(userPicks),
      edit_type: editTypeValue
    };

    // hide the submit button and auto picks
    $('#submit_user_bracket').hide();
    $('#auto_picks').hide();
    $('#loading').show();

    $.ajax({
      type: formAction,
      url: url,
      data: data,
      success: function(result) {
        // show message
        
        $('#loading').hide();
        
        $("#message")
        .empty()
        .show()
        .append(result['message']);
        
        // show error
        $("#error")
        .empty()
        .show()
        .append(result['error']);

        if( multipleEdits && result['error'] === '') {
          $("#submit_user_bracket").show();
          $("#auto_picks").show();
        }
      }
    });

  }

  return(false);
}

function setUserPick(obj) {
  // set team user picked ex: 5 Utah
  const userPickedTeam = obj.text().trim();
  //console.log('setUserPick');

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
