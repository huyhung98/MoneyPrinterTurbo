chrome.alarms.create("autoUploadCheck", { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "autoUploadCheck") {
    checkAutoUpload();
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "CHECK_AUTO_UPLOAD_NOW") {
    checkAutoUpload();
    sendResponse({ status: "checking" });
    return true;
  }
  
  if (request.action === "START_TIKTOK_UPLOAD") {
    // Open a new tab to TikTok upload
    chrome.tabs.create({ url: "https://www.tiktok.com/tiktokstudio/upload?from=mpt" }, (tab) => {
      // Store the pending upload data so the content script can pick it up
      chrome.storage.local.set({
        pendingUpload: {
          tabId: tab.id,
          taskId: request.payload.taskId,
          videoUrl: request.payload.videoUrl,
          title: request.payload.title,
          timestamp: Date.now()
        }
      });
      sendResponse({ success: true, tabId: tab.id });
    });
    return true; // Keep message channel open for async response
  }
});

let isQueueProcessing = false;

async function checkAutoUpload() {
  if (isQueueProcessing) return;
  
  chrome.storage.local.get(['autoUploadEnabled', 'uploadedTasks'], async (result) => {
    if (!result.autoUploadEnabled) return;
    
    isQueueProcessing = true;
    
    try {
      const uploadedTasks = result.uploadedTasks || [];
      const response = await fetch('http://127.0.0.1:8080/api/v1/tasks?page=1&page_size=20');
      if (!response.ok) throw new Error("API error");
      
      const data = await response.json();
      if (data.status === 200 && data.data && data.data.tasks) {
        // Find tasks that have videos and are NOT in uploadedTasks
        const newTasks = data.data.tasks.filter(task => 
          task.videos && task.videos.length > 0 && !uploadedTasks.includes(task.task_id)
        );
        
        // Reverse to process oldest first
        newTasks.reverse();
        
        for (const task of newTasks) {
          const title = task.params && task.params.video_subject ? task.params.video_subject : 'Untitled Video';
          const videoUrl = `http://127.0.0.1:8080/api/v1/download/${task.videos[0]}`;
          
          console.log(`Auto-uploading: ${title}`);
          await processSingleUpload(task.task_id, videoUrl, title);
        }
      }
    } catch (e) {
      console.error("Auto upload check failed", e);
    } finally {
      isQueueProcessing = false;
    }
  });
}

function processSingleUpload(taskId, videoUrl, title) {
  return new Promise((resolve) => {
    chrome.tabs.create({ url: "https://www.tiktok.com/tiktokstudio/upload?from=mpt" }, (tab) => {
      chrome.storage.local.set({
        pendingUpload: {
          tabId: tab.id,
          taskId: taskId,
          videoUrl: videoUrl,
          title: title,
          timestamp: Date.now()
        }
      });
      
      // Wait for content script to finish and mark it as uploaded in storage
      // We will poll storage every 5 seconds, timeout after 3 minutes.
      let checks = 0;
      const interval = setInterval(() => {
        checks++;
        chrome.storage.local.get(['uploadedTasks', 'pendingUpload'], (result) => {
          const uploaded = result.uploadedTasks || [];
          const pending = result.pendingUpload;
          
          // It's considered done if it's in uploaded array, OR if pendingUpload is cleared and 10 seconds passed
          // But to be safe, we just wait until it hits uploaded array or timeout.
          if (uploaded.includes(taskId) || checks > 36) { 
            clearInterval(interval);
            
            // Optionally close the tab if we wanted to be super clean, 
            // but closing it too fast might abort the network request TikTok sends.
            // So we'll just leave it open for the user to see it succeeded.
            resolve();
          }
        });
      }, 5000);
    });
  });
}
