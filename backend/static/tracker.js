(function() {
  'use strict';

  var script = document.querySelector('script[data-domain][data-token]');
  if (!script) return;

  // var domain = script.getAttribute('data-domain');
  var token  = script.getAttribute('data-token');
  var apiUrl = script.getAttribute('data-api') || script.src.replace(/\/js\/tracker\.js$/, '') + '/api/event';

  // Visitor ID (persistent)
  var STORAGE_KEY = '_metrika_vid';
  var visitorId = localStorage.getItem(STORAGE_KEY);
  if (!visitorId) {
    visitorId = crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
    localStorage.setItem(STORAGE_KEY, visitorId);
  }

  // Collect data
  var payload = {
    visitor_id:   visitorId,
    url:          location.href,
    referrer:     document.referrer || '',
    timezone:     Intl.DateTimeFormat().resolvedOptions().timeZone || ''
  };

  // Send 
  var xhr = new XMLHttpRequest();
  xhr.open('POST', apiUrl);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.setRequestHeader('X-Tracking-Token', token);
  xhr.send(JSON.stringify(payload));
})();