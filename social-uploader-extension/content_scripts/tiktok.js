// This script runs on https://www.tiktok.com/upload*

console.log("MPT TikTok Uploader Content Script loaded.");

let isProcessing = false;

function checkForPendingUpload() {
  if (isProcessing) return;

  // Only run if we are actually on an upload page
  if (!window.location.href.includes('upload')) {
    return;
  }

  chrome.storage.local.get(['pendingUpload'], async (result) => {
    const pending = result.pendingUpload;
    
    if (!pending) return;
    
    // Check if it's recent (e.g., within 5 mins) to avoid old tasks triggering
    if (Date.now() - pending.timestamp > 5 * 60 * 1000) {
      chrome.storage.local.remove('pendingUpload');
      return;
    }
    
    console.log("Found pending upload task:", pending);
    isProcessing = true;
    
    try {
      await processUpload(pending.videoUrl, pending.title, pending.taskId);
      // Clear it ONLY after successful processing to survive redirects
      chrome.storage.local.remove('pendingUpload');
    } catch (error) {
      console.error("Auto-upload failed:", error);
      // Removed alert to prevent blocking automation
      isProcessing = false;
    }
  });
}

// Check initially
checkForPendingUpload();

// Also check when storage changes (in case SPA hasn't reloaded)
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.pendingUpload && changes.pendingUpload.newValue) {
    setTimeout(checkForPendingUpload, 1000); // give the SPA time to route
  }
});

async function processUpload(videoUrl, title, taskId) {
  console.log(`Downloading video from ${videoUrl}...`);
  // Fetch the video file
  const response = await fetch(videoUrl);
  if (!response.ok) throw new Error("Failed to download video from MoneyPrinterTurbo server.");
  const blob = await response.blob();
  
  // Create a File object
  const file = new File([blob], "video.mp4", { type: 'video/mp4' });
  console.log("Video downloaded, size:", file.size);
  
  // TikTok SPA needs to load the upload UI
  await sleep(2000);
  
  const fileInput = await waitForElement('input[type="file"], input[accept="video/*"]', 10000);
  
  if (fileInput) {
    // Simulate user selecting the file
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    
    // Dispatch change event to trigger TikTok's React handlers
    const event = new Event('change', { bubbles: true });
    fileInput.dispatchEvent(event);
    
    console.log("File injected into input[type=file].");
  } else {
    console.warn("File input not found. Trying dropzone fallback...");
    // Attempt drag and drop simulation fallback
    const dropzone = document.querySelector('div[data-tt="upload_area"]') || document.body;
    
    const dropEvent = new Event('drop', { bubbles: true });
    Object.defineProperty(dropEvent, 'dataTransfer', {
      value: {
        files: [file],
        types: ['Files']
      }
    });
    dropzone.dispatchEvent(dropEvent);
  }
  
  // Wait for upload transition to finish and caption field to appear
  console.log("Waiting for caption field...");
  await sleep(4000); 
  
  // TikTok uses Draft.js or similar for captions
  const captionEditor = await waitForElement('.public-DraftEditor-content, [data-contents]', 15000);
  if (captionEditor) {
    captionEditor.focus();
    // Inject text using execCommand
    document.execCommand('insertText', false, title);
    console.log("Caption injected.");
  } else {
    console.warn("Caption editor not found.");
  }
  
  console.log("Waiting for Post button to become active...");
  let postButton = null;
  // Poll for up to 60 seconds to allow for video processing and copyright checks
  for (let i = 0; i < 60; i++) {
    postButton = Array.from(document.querySelectorAll('button, div[role="button"]')).find(b => 
      b.textContent.trim().toLowerCase() === 'post' && !b.disabled && b.getAttribute('aria-disabled') !== 'true'
    );
    if (postButton) {
      break;
    }
    await sleep(1000);
  }

  if (postButton) {
    console.log("Clicking Post button...");
    // Sometimes click events need to be dispatched if normal click doesn't work in React
    postButton.click();
    console.log("Post clicked!");
    
    // Check for "Continue to post?" modal that appears if copyright check is incomplete
    await sleep(2000);
    const confirmPostButton = Array.from(document.querySelectorAll('button')).find(b => 
      b.textContent.trim().toLowerCase() === 'post now' || b.textContent.trim().toLowerCase() === 'post anyway'
    );
    
    if (confirmPostButton) {
      console.log("Confirmation modal detected. Clicking Post now...");
      confirmPostButton.click();
      await sleep(1000);
    }
    
    // Save to uploaded list
    if (taskId) {
      chrome.storage.local.get(['uploadedTasks'], (result) => {
        const uploaded = result.uploadedTasks || [];
        if (!uploaded.includes(taskId)) {
          uploaded.push(taskId);
          chrome.storage.local.set({ uploadedTasks: uploaded });
        }
      });
    }
    
    console.log("Video successfully auto-posted to TikTok!");
  } else {
    console.warn("Post button not found or remained disabled. You may need to click it manually.");
    // Removed alert to prevent blocking automation
  }
}

function waitForElement(selector, timeout = 10000) {
  return new Promise((resolve) => {
    const el = document.querySelector(selector);
    if (el) return resolve(el);
    
    const observer = new MutationObserver((mutations, me) => {
      const el = document.querySelector(selector);
      if (el) {
        me.disconnect();
        resolve(el);
      }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, timeout);
  });
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}
