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


$("input.search").change(function() {
  if ($(this).val() != "") {
    $(this).addClass('filled');
  } else {
    $(this).removeClass('filled');
  }
})


Vue.config.devtools = true;

new Vue({
  el: '#app',
  delimiters: ['${', '}'],
  data: {
    count: 0,
    beers: [],
    visible: [],
    venues: [{'name': null, 'id': -1}],
    activeIdx: -1,
    selected_venue: {},
  },
  mounted: function() {
    this.getVenues('api/v1/venues/');
    this.getBeers();

    let component = this;
    $(".chosen-select").chosen().change(function ($event) {
      component.getVenueBeers($($event.target).val());
    });;
  },
  methods: {
    getBeers: function() {
      axios.get('api/v1/beers/').
      then((response) => {
        this.beers = response.data.results;
        for (var i = 0; i < this.beers.length; i++) {
          this.visible[i] = false;
          this.beers[i].styleObj = {
            '--background-color': this.beers[i].color_srm_html,
          };
        }
        this.activeIdx = -1;
        this.count = response.data.count;
      })
        .catch((err) => {
        console.log(err);
      });
    },
    getVenueBeers: function(venue) {
      axios.get('api/v1/venues/' + venue + '/').
      then((response) => {
        this.selected_venue = response.data;
      })
      .catch((err) => {
        console.log(err);
      });

      axios.get('api/v1/venues/' + venue + '/beers/').
      then((response) => {
        this.beers = response.data.results;
      for (var i = 0; i < this.beers.length; i++) {
          this.visible[i] = false;
          this.beers[i].styleObj = {
            '--background-color': this.beers[i].color_srm_html,
          };
        }
        this.activeIdx = -1;
        this.count = response.data.count;
      })
       .catch((err) => {
        console.log(err);
      });
    },
    getVenues: function(link) {
      axios.get(link).
      then((response) => {
        this.venues.push.apply(this.venues, response.data.results);
        $(".chosen-select").chosen().trigger("chosen:updated");
        if (response.data.next)
        {
          this.getVenues(response.data.next);
        }
      })
      .catch((err) => {
        console.log(err);
      });
    },
    onVenueChange(event) {
      if (event.target.value != -1)
        this.getVenueBeers(event.target.value);
      else
        this.getBeers();
    },
  },
});
