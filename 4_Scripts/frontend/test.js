const { chromium } = require('playwright'); // if playwright is installed, else use a simple fetch

async function run() {
  try {
    const res = await fetch('http://localhost:5173/');
    const text = await res.text();
    console.log("Page fetched successfully. Length: ", text.length);
  } catch (e) {
    console.error(e);
  }
}
run();
