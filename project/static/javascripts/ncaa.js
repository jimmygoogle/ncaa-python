let userPicks = {};
let upsetBonus = {};
let preloadedUpsetData;

$(window).on('load', function() {
  // load upset bonus data from dom on bottom of page (db)
  if (preloadedUpsetData) {
    upsetBonus = preloadedUpsetData;
  }

  loadUserPicks();
  setupPlayerBracket();
 });

function setupPlayerBracket() {
  // control bracket flow
  $('li').click(function() {
    setUserPick($(this));
  });

  // show/hide auto picks
  $('.picks-header').click(function() {
    $('.auto-picks-buttons').toggle();
  });

  // reset/clear auto picks
  $('#reset').click(function(event){
    event.preventDefault();
    resetPicks();
  });

  // pick all favorites
  $('#chalk').click(function(event){
    event.preventDefault();
    makePicks('chalk');
  });

  // make weighted picks
  $('#mix').click(function(event){
    makePicks('mix');
  });

  // make random picks
  $('#random').click(function(event){
    makePicks('random');
  });

  // validate and submit user bracket form
  $('#submit_user_bracket').click(function(event) {
    event.preventDefault();
    data = validateUserInput();

    if(data) {
      submitBracket(data);
    }
  });
}

function toggleDisplayForPicks() {
  $('.auto-picks').toggle();
  $('.bracket_details').toggle();
}

function resetPicks() {
  // loop through all games and reset picks
  for (let index = 33; index <= 63; index++) {

    $('.game' + index).find('li').each(function(){
      $(this).empty();
      $(this).attr('data-team-id', '');
    });
  }

  userPicks = {};
  upsetBonus = {};
}

function makePicks(type) {
  let game = '';
  let games = [];
  
  // added some weighting for seeds by round
  // https:// www.betfirm.com/seeds-national-championship-odds/
  const weights = {
    1 : {
      1 : 0.993,
      2 : 0.932,
      3 : 0.851,
      4 : 0.791,
      5 : 0.642,
      6 : 0.615,
      7 : 0.608,
      8 : 0.486,
      9 : 0.514,
      10 : 0.392,
      11 : 0.385,
      12 : 0.358,
      13 : 0.209,
      14 : 0.149,
      15 : 0.068,
      16 : 0.007
    },
    2 : {
      1 : 0.851,
      2 : 0.628,
      3 : 0.52,
      4 : 0.473,
      5 : 0.338,
      6 : 0.291,
      7 : 0.189,
      8 : 0.101,
      9 : 0.047,
      10 : 0.161,
      11 : 0.176,
      12 : 0.149,
      13 : 0.041,
      14 : 0.014,
      15 : 0.002,
      16 : 0.0
    },
    3 : {
      1 : 0.682,
      2 : 0.453,
      3 : 0.25,
      4 : 0.149,
      5 : 0.068,
      6 : 0.101,
      7 : 0.068,
      8 : 0.061,
      9 : 0.027,
      10 : 0.061,
      11 : 0.061,
      12 : 0.014,
      13 : 0.0,
      14 : 0.0,
      15 : 0.0,
      16 : 0.0
    },
    4 : {
      1 : 0.405,
      2 : 0.216,
      3 : 0.115,
      4 : 0.088,
      5 : 0.047,
      6 : 0.02,
      7 : 0.02,
      8 : 0.041,
      9 : 0.007,
      10 : 0.007,
      11 : 0.034,
      12 : 0.0,
      13 : 0.0,
      14 : 0.0,
      15 : 0.0,
      16 : 0.0
    },
    5 : {
      1 : 0.25,
      2 : 0.088,
      3 : 0.074,
      4 : 0.02,
      5 : 0.02,
      6 : 0.014,
      7 : 0.007,
      8 : 0.027,
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
      1 : 0.162,
      2 : 0.034,
      3 : 0.027,
      4 : 0.007,
      5 : 0.0,
      6 : 0.007,
      7 : 0.007,
      8 : 0.007,
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
      const teamInfo = $(this).text().trim().split(' ');
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

  if(editTypeValue == 'add') {
    return false;
  }

  $('#bracket').find('li').each(function() {      
    const slotData = $(this).attr('id').match(/slot(\d+)/);
    const startSlot = (bracketType == 'sweetSixteenBracket') ? 113 : 65;

    if(slotData[1] >= startSlot) {
      const teamId = $(this).attr('data-team-id');
      const gameId = slotData[1] - 64;

      if(teamId > 0) {
        userPicks[gameId] = teamId;
      }        
    }
  });

  const winnerTeamId = $('#ncaaWinner').attr('data-team-id');
  if(winnerTeamId > 0) {
    userPicks[63] = winnerTeamId;
  }
  // console.log(userPicks);
  // console.log(upsetBonus);
}

function validateUserInput() {
  let status = true;
  const $userBracketInfoForm = $('#userBracketInfoForm');
  const editTypeValue = $userBracketInfoForm.find('#editType').val();
  const bracketTypeName = $userBracketInfoForm.find('#bracketType').val();
  const bracketTypeLabel = $userBracketInfoForm.find('#bracketTypeLabel').val();  
  const emailAddress = $userBracketInfoForm.find('#email').val();
  const username = $userBracketInfoForm.find('#username').val();
  const firstName = $userBracketInfoForm.find('#firstname').val();
  const tieBreakerPoints = parseInt($userBracketInfoForm.find('#tieBreaker').val());

  let error_message;
  // get rid of error messages once the pool is submitted
  $("#error").empty();

  if(editTypeValue !== 'admin') {
    // the expected number of user picks changes based on the bracket type
    const expectedNumberOfGames = (bracketTypeName == 'sweetSixteenBracket') ? 15 : 63;

    // make sure all games are filled in when we are filling out a bracket
    if(status && Object.keys(userPicks).length !== expectedNumberOfGames && (editTypeValue == 'add')) {
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

    if(status && (tieBreakerPoints < 100 || tieBreakerPoints > 300)) {
      error_message = 'Please enter a valid guess<br>for your total points.';
      $userBracketInfoForm.find('#tieBreaker').focus();
      status = false;
    }

    // # TOOO this shouldnt return a 200
    // tell user if the user name is already used
    if(status) {
      if((editTypeValue !== 'edit') && (editTypeValue !== 'admin')) {
        $.ajax({
          async: false,
          type: 'POST',
          url: location.protocol + '//' + location.host + '/bracket/user',
          data: {
            username,
            bracket_type: bracketTypeName
          },
          success: function(result) {
            error_message = result['error'];
          }
        });
      }
    }
  }

  // show error message
  if(error_message) {
    $("#error")
    .empty()
    .append(error_message);
    return false;
  }

  return {
    email_address: emailAddress,
    username: username,
    first_name: firstName,
    tie_breaker_points: tieBreakerPoints,
    bracket_type_name: bracketTypeName,
    bracket_type_label: bracketTypeLabel,
    user_picks: JSON.stringify(userPicks),
    upset_bonus: JSON.stringify(upsetBonus),
    edit_type: editTypeValue
  };
}

function submitBracket(data) {
  let formAction = 'POST';
  let multipleEdits = false;

  // this is kind a hack for the bracket router
  const rand_string = Math.random().toString(36).substring(7);
  let url = window.location.href + 'bracket/' + data['bracket_type_label'] + '/' + rand_string;

  if( (data['edit_type'] == 'admin') || (data['edit_type'] == 'edit')) {
    multipleEdits = true;
    formAction = 'PUT';
    url = window.location.href;
  }

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

  return(false);
}

function setUserPick(obj) {
  // set team user picked ex: 5 Utah
  // console.log(obj.html());
  const userPickedTeam = obj.text().trim();
  const pickedTeamData = userPickedTeam.split(' ');
  const userPickedSeed = parseInt(pickedTeamData[0]);
  // console.log('setUserPick');

  // get game number and all possible game slots that the user pick could play in
  // ex: class = "matchup game1 65|97|113|121|125" (we need the 2nd and 3rd element)
  const gameData = obj.parent().attr('class').split(' ');

  const gameSlots = obj.parent().attr('data-games');
  const teamId = obj.attr('data-team-id');

  // we want to not allow the user to edit any games previous played if we are in the sweet 16
  const game = gameData[1].match(/game(\d+)/);

  // get other team id
  let otherTeamId;
  $( '.' + gameData[1]).find('li').each(function() {
    if (userPickedTeam != $.trim( $(this).text() ) ) {
      otherTeamId = $(this).attr('data-team-id');
    }
  });

  if((game[1] < 49) && $('#bracketType').val() == 'sweetSixteenBracket') {
    return;
  }

  // clear all previous picks (in case user is changing pick)
  const otherGameSeed = clearPreviousPicks(gameData[1], userPickedTeam, gameSlots);

  // figure out if the pick is eligble for an upset bonus
  let upsetBonusFlag = 0;

  // console.log("userPickedSeed is "  + userPickedSeed);
  // console.log("otherGameSeed is "  + otherGameSeed);

  if (otherGameSeed && (userPickedSeed > otherGameSeed)) {
    upsetBonusFlag = 1;
  }

  // console.log(userPickedSeed);
  // console.log(otherGameSeed);
  // console.log("upsetBonusFlag is " + upsetBonusFlag);

  // set data so it can be submitted to DB
  setUserFormData(gameData[1], teamId, upsetBonusFlag);

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
      userPicks[63] = teamId;
    }
    else {
      // set new pick
      const $slot = $('#slot' + newSlot);
      $slot.attr('data-team-id', teamId);
      $slot.empty().append(obj.html());
    }
  }
  // console.log(userPicks);
  // console.log(upsetBonus);
}

function setUserFormData(gameData, teamId, upsetBonusFlag) {
  const gameId = parseInt(gameData.match(/\d+/));
  userPicks[gameId] = teamId;
  upsetBonus[gameId] = upsetBonusFlag;
}

function clearPreviousPicks(gameNumber, userPickedTeam, slotString) {
  // get the 'other' team in the current game the user is picking
  const otherTeamData = _getOtherTeamInGame(gameNumber, userPickedTeam);
  const getOtherTeamInGame = otherTeamData['teamName'];
  const teamId = otherTeamData['teamId'];
  // console.log('other team in game is ' + getOtherTeamInGame);

  if(getOtherTeamInGame){
    // only check (match) specified slots (ex 81|105|119|127)
    const slotMatch = eval('/' + slotString + '/');

    // check the rest of the bracket now for the existence of the 'other team' and remove it
    // this is needed for when the user changes their pick(s)
    let pick;
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
        pick = $.trim($(this).text());

        // get rid of all future picks that match
        if(pick !== '' && getOtherTeamInGame.match(pick)){
          console.log("slotNumber is " + slotNumber);
          $(this).empty();

          const teamId = $(this).attr('data-team-id');
          const gameId = slotNumber - 64;
          // console.log("we are going to delete game " + gameId);

          delete userPicks[gameId];
          $(this).attr('data-team-id', '');
        }
      }
    });

    // clean out champion if the user picked someone to beat the champion
    if (pick && teamId == userPicks[63] ) {
      delete userPicks[63];
    }

    // return seed
    const team_data = getOtherTeamInGame.split(' ');
    return parseInt(team_data[0]);
  }
}

function _getOtherTeamInGame(gameNumber, userPickedTeam) {
  let teamsInGame = [];

  // get both teams in game
  $( '.' + gameNumber).find('li').each(function() {
    // clean string and put into array
    teamsInGame.push({
      teamName: $.trim( $(this).text() ),
      teamId: $(this).attr('data-team-id')
    });
  });

  let arrayIndex = teamsInGame.findIndex(x => x.teamName  === userPickedTeam);

  if(arrayIndex == 0) {
    arrayIndex++;
  }
  else {
    arrayIndex--;
  }

  return(teamsInGame[ arrayIndex ]);
}
