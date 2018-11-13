$(document).ready (function() {
  $("#cssmenu").menumaker({
    format: "multitoggle"
  });

  setFinalGame();
  setStandings();
});

function setFinalGame() {
  const winner = $('#bracket').find('#ncaaWinner').attr('data-team-id');
  const pickCss = $('#bracket').find('#ncaaWinner').attr('data-pick');

  if(!winner) {
    return false;
  }

  $('.game63').find('li').each(function(){
    const teamID = $(this).attr('data-team-id');

    if(teamID === winner) {
      // set winner
      $(this).addClass('winner');
      
      // set the correct pick class for the winner
      // if they picked the right team in the final but they lost then we need to show that
      $(this).removeClass('incorrectPick');
      $(this).removeClass('correctPick');
      $(this).addClass(pickCss);
    }
  });
}

function setStandings() {
  //make all rows in standings clickable
  $('.standings').find('tr').click(function() {
    const href = $(this).find("a").attr("href");
    if(href) {
        window.location = href;
    }
  });
}

// menu logic copied from codepen.io
(function($) {
  $.fn.menumaker = function(options) {
   var cssmenu = $(this), settings = $.extend({
     format: "dropdown",
     sticky: false
   }, options);
   return this.each(function() {
     $(this).find(".button").on('click', function(){
       $(this).toggleClass('menu-opened');
       var mainmenu = $(this).next('ul');
       if (mainmenu.hasClass('open')) {
         mainmenu.slideToggle().removeClass('open');
       }
       else {
         mainmenu.slideToggle().addClass('open');
         if (settings.format === "dropdown") {
           mainmenu.find('ul').show();
         }
       }
     });
     cssmenu.find('li ul').parent().addClass('has-sub');
  multiTg = function() {
       cssmenu.find(".has-sub").prepend('<span class="submenu-button"></span>');
       cssmenu.find('.submenu-button').on('click', function() {
         $(this).toggleClass('submenu-opened');
         if ($(this).siblings('ul').hasClass('open')) {
           $(this).siblings('ul').removeClass('open').slideToggle();
         }
         else {
           $(this).siblings('ul').addClass('open').slideToggle();
         }
       });
     };
     if (settings.format === 'multitoggle') multiTg();
     else cssmenu.addClass('dropdown');
     if (settings.sticky === true) cssmenu.css('position', 'fixed');
  resizeFix = function() {
    var mediasize = 700;
       if ($( window ).width() > mediasize) {
         cssmenu.find('ul').show();
       }
       if ($(window).width() <= mediasize) {
         cssmenu.find('ul').hide().removeClass('open');
       }
     };
     resizeFix();
     return $(window).on('resize', resizeFix);
   });
    };
  })(jQuery);