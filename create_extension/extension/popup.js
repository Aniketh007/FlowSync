document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const autoShareToggle = document.getElementById('autoShareToggle');
  const autoShareDescription = document.getElementById('autoShareDescription');
  const shareButton = document.getElementById('shareButton');
  const statusMessage = document.getElementById('statusMessage');
  const lastSharedContainer = document.getElementById('lastSharedContainer');
  const lastSharedTime = document.getElementById('lastSharedTime');
  
  // Load initial state
  loadAutoShareState();
  loadLastShared();
  
  // Set up event listeners
  autoShareToggle.addEventListener('change', toggleAutoShare);
  shareButton.addEventListener('click', shareAllTabs);
  
  // Function to load auto-share state
  function loadAutoShareState() {
    chrome.runtime.sendMessage({ action: "getAutoShareStatus" }, function(response) {
      autoShareToggle.checked = response.autoShareEnabled;
      updateAutoShareDescription(response.autoShareEnabled);
    });
  }
  
  // Function to load last shared information
  function loadLastShared() {
    chrome.storage.local.get(['lastShared'], function(result) {
      if (result.lastShared) {
        const lastSharedDate = new Date(result.lastShared);
        lastSharedTime.textContent = formatRelativeTime(lastSharedDate);
        lastSharedContainer.style.display = 'block';
      } else {
        lastSharedContainer.style.display = 'none';
      }
    });
  }
  
  // Function to toggle auto-share
  function toggleAutoShare() {
    const enabled = autoShareToggle.checked;
    chrome.runtime.sendMessage({
      action: "setAutoShare", 
      enabled: enabled
    }, function(response) {
      if (response.success) {
        updateAutoShareDescription(response.autoShareEnabled);
        if (response.autoShareEnabled) {
          setStatus('Auto-sharing enabled. The AI Assistant now has access to all your tabs.', 'success');
          shareButton.disabled = true;
        } else {
          setStatus('Auto-sharing disabled.', 'success');
          shareButton.disabled = false;
        }
      }
    });
  }
  
  // Function to update description based on auto-share state
  function updateAutoShareDescription(enabled) {
    if (enabled) {
      autoShareDescription.textContent = 'AI Assistant automatically receives content from all your open tabs.';
      shareButton.disabled = true;
    } else {
      autoShareDescription.textContent = 'When enabled, the AI Assistant will automatically have access to all open tabs.';
      shareButton.disabled = false;
    }
  }
  
  // Function to share all tabs
  function shareAllTabs() {
    shareButton.disabled = true;
    setStatus('Sharing all tabs...', '');
    
    chrome.runtime.sendMessage({ action: "shareAllTabs" }, function(response) {
      if (response.success) {
        setStatus('Tabs shared successfully! The AI Assistant can now answer questions based on them.', 'success');
      } else {
        setStatus(`Error: ${response.message}`, 'error');
      }
      shareButton.disabled = false;
      loadLastShared();
    });
  }
  
  // Function to set status message
  function setStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = 'status ' + type;
  }
  
  // Function to format relative time
  function formatRelativeTime(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleString();
    }
  }
});
