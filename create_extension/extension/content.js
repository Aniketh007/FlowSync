// This script runs in the context of web pages
// It can be used to handle more complex content extraction if needed

// Listen for any direct messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getPageInfo") {
    const pageInfo = {
      title: document.title,
      url: window.location.href,
      textContent: document.body.innerText.substring(0, 5000)
    };
    sendResponse(pageInfo);
  }
  return true;
});

// Log when the script is injected
console.log('Active Tab Reader content script loaded');
