chrome.app.runtime.onLaunched.addListener(function(launchData) {
  chrome.app.window.create(
    'app/index.html', {
      id: "NereidProject",
      minWidth: 500,
      minHeight: 600,
    });
});
