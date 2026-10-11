// Stream Deck hides the plugin document and suspends its window timers.
// A worker keeps the animation clock running while keys are visible.
setInterval(() => postMessage(null), 1000 / 20);
