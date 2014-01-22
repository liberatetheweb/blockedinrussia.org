$(function() {
 	localizeAll($.cookie('lang'));
  $('#en').click(function() { $.cookie('lang', 'en', { expires: 365 }); localizeAll('en'); });
  $('#ru').click(function() { $.cookie('lang', 'ru', { expires: 365 }); localizeAll('ru'); });
  $('#form').on('submit', function(e){
    e.preventDefault();
    $('#loading').addClass('fa fa-spinner fa-spin');
    if ($('#input').val().search(/^https?:\/\//) == '-1') {
      var url = 'http://' + $('#input').val();
    }
    else {
      var url = $('#input').val();
    }
    $.get('/check', {url: url}, function(data) {
      var map = L.map('map').setView([61.77, 100.72], 3);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Data &copy; by <a href="http://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>.',
        maxZoom: 18
      }).addTo(map);
      $('#registry').html('');
      $('#results').html('');
      $('#blocked').removeClass('hidden');
      $('#loading').removeClass('fa fa-spinner fa-spin');
      $('#registry').append('IP: ' + data.ip.join(', ') + '<br>');
      if (data.registry[0]) {
        $('#registry').removeClass('alert-success').addClass('alert-danger');
        $('#registry').append(
          '<table class="table"><thead><tr>' +
          '<th>URL</th><th>IP</th><th data-l10n="authority">' + l('authority', 'Authority') + '</th>' +
          '<th data-l10n="base">' + l('base','Base') +
          '</th><th data-l10n="date">' + l('date','Date') + '</th>' +
          '</tr></thead><tbody></tbody></table>'
        );
        for (i in data.registry) {
          $('#registry > table > tbody').append(
            '<tr>' +
              '<th>' + data.registry[i].url.join(', ') + '</th>' +
              '<th>' + data.registry[i].ip.join(', ') + '</th>' +
              '<th>' + data.registry[i].authority + '</th>' +
              '<th>' + data.registry[i].base + '</th>' +
              '<th>' + data.registry[i].date + '</th>' +
            '</tr>'
          );
        }
      }
      else {
        $('#registry').append(l('not-banned','Not in Russia\'s internet blacklist and not in Russia\'s piracy blacklist.'));
        $('#registry').removeClass('alert-danger').addClass('alert-success');
      }
      for (i in data.results) {
        if (data.results[i].blocked == 'yes') {
          var panelclass = 'panel-danger';
          var icon = L.AwesomeMarkers.icon({
            icon: 'lock',
            markerColor: 'red',
            prefix: 'fa'
          });
        }
        else if (data.results[i].blocked == 'no') {
          var panelclass = 'panel-success';
          var icon = L.AwesomeMarkers.icon({
            icon: 'unlock',
            markerColor: 'green',
            prefix: 'fa'
          });
        }
        else if (data.results[i].blocked == 'maybe') {
          var panelclass = 'panel-warning';
          var icon = L.AwesomeMarkers.icon({
            icon: 'question',
            markerColor: 'orange',
            prefix: 'fa'
          });
        }
        if (data.results[i].status != 'fail') {          
          $('#results').append(
            '<div class="col-md-3"><div class="panel ' + panelclass + '"><div class="panel-body">' +
              '<span data-l10n="isp">' + l('isp','ISP') + '</span>: ' + data.results[i].as_name + '<br>' + 
              '<span data-l10n="http-code">' + l('http-code','HTTP code') + '</span>: ' + data.results[i].status + '<br>' +
              '<span data-l10n="blocked">' + l('blocked','Blocked') + '</span>: ' + l(data.results[i].blocked,data.results[i].blocked)  +
            '</div></div></div>'
          );
        }
        if (data.results[i].status != 'fail') {
          var marker = L.marker([data.results[i].lat, data.results[i].lon], {icon: icon}).addTo(map);
          marker.bindPopup(
            '<p>' + l('isp','ISP') + ': ' + data.results[i].as_name + '<br>' + 
            l('http-code','HTTP code') + ': ' + data.results[i].status + '<br>' +
            l('blocked','Blocked') + ': ' + l(data.results[i].blocked,data.results[i].blocked) + '</p>'
          );
        }
      }
    }, 'json');
  });
});



function l(string, fallback) {
	var localized = string.toLocaleString();
	if (localized !== string) {
		return localized;
	} else {
		return fallback;
	}
}

function localizeAll(lang) {
	if (!lang) return;
	String.locale = lang;
	$('[data-l10n]').each(function(i) {
		$(this).html(l($(this).attr('data-l10n'),$(this).html()));
	});
  $('#input').attr('placeholder', l('placeholder', 'URL to check'));
	document.documentElement.lang = String.locale;
}

String.prototype.join = function () {return this.toString(); };
