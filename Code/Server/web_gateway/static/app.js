const ws = new WebSocket(`ws://${location.host}/ws`);

function sendKey(eventType, key) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ "event": eventType, "key": key }));
  }
}

// Keyboard controls
window.addEventListener('keydown', e => {
  if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) {
    e.preventDefault();
    sendKey('down', e.key);
  } else if (["w","s","a","d"].includes(e.key)) {
    sendKey('down', e.key);
  }
}, { passive: false });

window.addEventListener('keyup', e => {
  if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) {
    e.preventDefault();
    sendKey('up', e.key);
  } else if (["w","s","a","d"].includes(e.key)) {
    sendKey('up', e.key);
  }
}, { passive: false });

