const ws = new WebSocket(`ws://${location.host}/control`);

function sendKey(eventType, key) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ "event": eventType, "key": key }));
  }
}

// Keyboard controls
window.addEventListener('keydown', e => {
  console.log(`Key down: ${e.key}`);
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



let lastSent = 0;
const SEND_INTERVAL_MS = 100; // 10 times per second

window.addEventListener("gamepadconnected", (event) => {
  const gp = event.gamepad;
  console.log(`Gamepad connected: ${gp.id}`);
  requestAnimationFrame(updateGamepad);
});

function updateGamepad() {
  const gamepads = navigator.getGamepads();
  const gp = gamepads[0]; // assuming one controller

  if (gp && ws.readyState === WebSocket.OPEN) {
      const now = performance.now();
      if (now - lastSent > SEND_INTERVAL_MS) {
        const command = {
          throttle: -gp.axes[1],
          steering: gp.axes[0],
        };
        ws.send(JSON.stringify({ "event": "joystick_axes", "command": command }));

        const aPressed = gp.buttons[0].pressed;
        const bPressed = gp.buttons[1].pressed;
        const xPressed = gp.buttons[2].pressed;
        const yPressed = gp.buttons[3].pressed;
        lastSent = now;
      }
    }

  requestAnimationFrame(updateGamepad);
}

window.addEventListener("gamepaddisconnected", (event) => {
  console.log(`Gamepad disconnected: ${event.gamepad.id}`);
});



// Virtual joystick touch controls
const joystickZone = document.getElementById('joystick-zone');
const joystickKnob = document.getElementById('joystick-knob');
const JOYSTICK_RADIUS = 75; // half of zone width/height

let joystickTouchId = null;

function sendJoystickAxes(throttle, steering) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ event: "joystick_axes", command: { throttle, steering } }));
  }
}

function updateJoystick(clientX, clientY) {
  const rect = joystickZone.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;

  let dx = clientX - cx;
  let dy = clientY - cy;

  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist > JOYSTICK_RADIUS) {
    dx = dx / dist * JOYSTICK_RADIUS;
    dy = dy / dist * JOYSTICK_RADIUS;
  }

  joystickKnob.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
  sendJoystickAxes(-dy / JOYSTICK_RADIUS, dx / JOYSTICK_RADIUS);
}

function resetJoystick() {
  joystickTouchId = null;
  joystickKnob.style.transform = 'translate(-50%, -50%)';
  sendJoystickAxes(0, 0);
}

joystickZone.addEventListener('touchstart', (e) => {
  e.preventDefault();
  if (joystickTouchId === null) {
    const touch = e.changedTouches[0];
    joystickTouchId = touch.identifier;
    updateJoystick(touch.clientX, touch.clientY);
  }
}, { passive: false });

joystickZone.addEventListener('touchmove', (e) => {
  e.preventDefault();
  for (const touch of e.changedTouches) {
    if (touch.identifier === joystickTouchId) {
      updateJoystick(touch.clientX, touch.clientY);
      break;
    }
  }
}, { passive: false });

joystickZone.addEventListener('touchend', (e) => {
  e.preventDefault();
  for (const touch of e.changedTouches) {
    if (touch.identifier === joystickTouchId) {
      resetJoystick();
      break;
    }
  }
}, { passive: false });

joystickZone.addEventListener('touchcancel', resetJoystick);



const telemetryWs = new WebSocket(`ws://${location.host}/telemetry`);

telemetryWs.onopen = () => {
    console.log("Telemetry connected");
};

const vEl = document.getElementById("v");
const iEl = document.getElementById("i");
const pEl = document.getElementById("p");

telemetryWs.onmessage = (event) => {
    const data = JSON.parse(event.data);

    vEl.textContent = data.voltage.toFixed(2);
    iEl.textContent = data.current.toFixed(2);
    pEl.textContent = data.power.toFixed(2);
};

telemetryWs.onclose = () => {
    console.log("Telemetry disconnected");
};
