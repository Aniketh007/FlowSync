// Configuration
const apiEndpoint = 'http://localhost:5000/active_tab';
let autoShareEnabled = false;

// Initialize stored preferences
chrome.storage.local.get(['autoShareEnabled'], function(result) {
  autoShareEnabled = result.autoShareEnabled === true;
});

// Listen for changes in auto-share setting
chrome.storage.onChanged.addListener(function(changes, namespace) {
  if (changes.autoShareEnabled) {
    autoShareEnabled = changes.autoShareEnabled.newValue === true;
  }
});

// Listen for tab updates (when a page finishes loading)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only proceed if the tab has completed loading and is active
  if (changeInfo.status === 'complete' && tab.active && autoShareEnabled) {
    setTimeout(() => shareAllTabs(true), 1000); // Wait a second for content to fully render
  }
});

// Listen for tab activation (when user switches tabs)
chrome.tabs.onActivated.addListener((activeInfo) => {
  if (autoShareEnabled) {
    setTimeout(() => shareAllTabs(true), 1000); // Wait a second for content to fully render
  }
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "shareAllTabs" || request.action === "shareActiveTab") {
    shareAllTabs(false).then(result => {
      sendResponse({ success: result.success, message: result.message });
    });
    return true; // Required for async response
  }
  
  if (request.action === "setAutoShare") {
    setAutoShare(request.enabled).then(result => {
      sendResponse({ success: true, autoShareEnabled: result });
    });
    return true; // Required for async response
  }
  
  if (request.action === "getAutoShareStatus") {
    chrome.storage.local.get(['autoShareEnabled'], function(result) {
      sendResponse({ autoShareEnabled: result.autoShareEnabled === true });
    });
    return true; // Required for async response
  }
});

// Function to enable/disable auto-sharing
async function setAutoShare(enabled) {
  autoShareEnabled = enabled === true;
  await chrome.storage.local.set({ autoShareEnabled: autoShareEnabled });
  
  // If enabling auto-share, immediately share all tabs
  if (autoShareEnabled) {
    await shareAllTabs(true);
  }
  
  return autoShareEnabled;
}

// Function to share all open tabs' content
async function shareAllTabs(isAutomatic) {
  try {
    // Get all tabs in the current window
    const tabs = await chrome.tabs.query({ currentWindow: true });
    // Filter out system pages
    const validTabs = tabs.filter(tab =>
      tab.url &&
      !tab.url.startsWith('chrome://') &&
      !tab.url.startsWith('chrome-extension://')
    );
    
    // Extract content from each tab
    const tabsData = await Promise.all(validTabs.map(async (tab) => {
      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          function: extractPageContent
        });
        if (!results || results.length === 0 || !results[0].result) {
          console.warn("No content extracted for tab:", tab);
          return null;
        }
        return {
          title: tab.title,
          url: tab.url,
          content: results[0].result
        };
      } catch (err) {
        console.error("Error extracting content for tab:", tab, err);
        return null;
      }
    }));
    
    // Filter out any tabs where content extraction failed
    const filteredTabsData = tabsData.filter(data => data !== null);
    
    // Debug log payload
    console.log("Sending payload:", { tabsData: filteredTabsData });
    
    // Send data to backend only if we have valid tab data
    if (!filteredTabsData.length) {
      throw new Error("No valid tab data to send.");
    }
    
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tabsData: filteredTabsData })
    });
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const responseData = await response.json();
    
    // Update last shared timestamp
    await chrome.storage.local.set({
      lastShared: new Date().toISOString()
    });
    
    return { 
      success: true, 
      message: isAutomatic ? "Tabs shared automatically" : "Tabs shared successfully" 
    };
    
  } catch (error) {
    console.error("Error sharing tabs:", error);
    return { 
      success: false, 
      message: `Error: ${error.message}`,
      silent: isAutomatic
    };
  }
}

// Function to extract content from a page
function extractPageContent() {
  // Get the page title
  const title = document.title;
  
  // Get meta description
  const metaDescription = document.querySelector('meta[name="description"]')?.content || '';
  
  // Get headings
  const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
    .map(h => ({
      level: h.tagName.toLowerCase(),
      text: h.textContent.trim()
    }))
    .filter(h => h.text.length > 0);
  
  // Try to find the main content
  const mainContent = 
    document.querySelector('main') || 
    document.querySelector('article') || 
    document.querySelector('#content') || 
    document.querySelector('.content') || 
    document.body;
  
  // Get text content (limit length)
  const textContent = mainContent.innerText.substring(0, 100000);
  
  // Get links
  const links = Array.from(document.querySelectorAll('a[href]'))
    .map(a => ({
      text: a.textContent.trim(),
      url: a.href
    }))
    .filter(l => l.text.length > 0)
    .slice(0, 20);
  
  // Get images
  const images = Array.from(document.querySelectorAll('img[src]'))
    .map(img => ({
      alt: img.alt,
      src: img.src
    }))
    .filter(img => img.src.length > 0)
    .slice(0, 10);
  
  return {
    title,
    metaDescription,
    headings,
    textContent,
    links,
    images,
    timestamp: new Date().toISOString()
  };
}
