import { NextResponse } from "next/server";

const DEFAULT_API_URL = "https://metrika-api.up.railway.app";

export const runtime = "edge";

function apiBase() {
  return (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL).replace(/\/+$/, "");
}

export async function GET() {
  const js = `
(function () {
  function uuidv4() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
    var s = [], hex = '0123456789abcdef';
    for (var i = 0; i < 36; i++) s[i] = hex[Math.floor(Math.random() * 16)];
    s[14] = '4';
    // @ts-ignore
    s[19] = hex[(parseInt(s[19], 16) & 0x3) | 0x8];
    s[8] = s[13] = s[18] = s[23] = '-';
    return s.join('');
  }

  function getVisitorId() {
    try {
      var key = 'metrika_visitor_id';
      var existing = localStorage.getItem(key);
      if (existing) return existing;
      var id = uuidv4();
      localStorage.setItem(key, id);
      return id;
    } catch (e) {
      return uuidv4();
    }
  }

  function getScript() {
    var s = document.currentScript;
    if (s && s.getAttribute) return s;
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      var el = scripts[i];
      if (el.getAttribute('data-token')) return el;
    }
    return null;
  }

  var script = getScript();
  if (!script) return;

  var token = script.getAttribute('data-token') || '';
  if (!token) return;

  var api = '${apiBase()}';
  var lastUrl = null;

  function send() {
    try {
      var url = location.href;
      if (url === lastUrl) return;
      lastUrl = url;

      var payload = {
        visitor_id: getVisitorId(),
        url: url,
        referrer: document.referrer || '',
        timezone: (Intl && Intl.DateTimeFormat ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC') || 'UTC'
      };

      fetch(api + '/api/events/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tracking-Token': token
        },
        body: JSON.stringify(payload),
        keepalive: true
      }).catch(function () {});
    } catch (e) {}
  }

  send();

  var pushState = history.pushState;
  var replaceState = history.replaceState;
  history.pushState = function () { pushState.apply(this, arguments); send(); };
  history.replaceState = function () { replaceState.apply(this, arguments); send(); };
  window.addEventListener('popstate', function () { send(); });
})();
`.trim();

  return new NextResponse(js, {
    headers: {
      "Content-Type": "application/javascript; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}

