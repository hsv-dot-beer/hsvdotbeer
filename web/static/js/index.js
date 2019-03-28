/*Bubble Animation - Credit: https://codepen.io/z-/pen/bpxgWZ */

function initparticles() {
   bubbles();
}

function bubbles() {
   $.each($(".particletext.bubbles"), function(){
      var bubblecount = ($(this).width()/50)*4;
      for(var i = 0; i <= bubblecount; i++) {
         var size = ($.rnd(40,80)/10);
         $(this).append('<span class="particle" style="top:' + $.rnd(0,60) + '%; left:' + $.rnd(0,95) + '%;width:' + size + 'px; height:' + size + 'px;animation-delay: ' + ($.rnd(0,30)/10) + 's;"></span>');
      }
   });
}

jQuery.rnd = function(m,n) {
      m = parseInt(m);
      n = parseInt(n);
      return Math.floor( Math.random() * (n - m + 1) ) + m;
}

initparticles();

$( ".beer" ).click(function() {
  $( this ).toggleClass( "active" );
});

$( ".search-icon" ).click(function() {
  $( this ).toggleClass( "active" );
});



 $("input.search").focus(function(){
   $(this).parent().addClass("active");

  }).blur(function(){
   $(this).parent().removeClass("active");
  });

$(".chosen-select").chosen()



$("input.search").change(function() {
  if ($(this).val() != "") {
    $(this).addClass('filled');
  } else {
    $(this).removeClass('filled');
  }
})