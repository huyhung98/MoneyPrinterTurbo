const API_URL = 'http://127.0.0.1:8080/api/v1';

document.addEventListener('DOMContentLoaded', () => {
  fetchTasks();
  
  const toggle = document.getElementById('auto-upload-toggle');
  
  // Load initial state
  chrome.storage.local.get(['autoUploadEnabled'], (result) => {
    toggle.checked = !!result.autoUploadEnabled;
  });
  
  // Handle toggle changes
  toggle.addEventListener('change', (e) => {
    const isEnabled = e.target.checked;
    chrome.storage.local.set({ autoUploadEnabled: isEnabled }, () => {
      if (isEnabled) {
        chrome.runtime.sendMessage({ action: "CHECK_AUTO_UPLOAD_NOW" });
      }
    });
  });
});

async function fetchTasks() {
  const loading = document.getElementById('loading');
  const videoList = document.getElementById('video-list');
  
  try {
    const response = await fetch(`${API_URL}/tasks?page=1&page_size=20`);
    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }
    const data = await response.json();
    
    // Get uploaded tasks from Chrome storage
    chrome.storage.local.get(['uploadedTasks'], (storageResult) => {
      const uploadedTasks = storageResult.uploadedTasks || [];
      
      loading.style.display = 'none';
      
      if (data.status === 200 && data.data && data.data.tasks && data.data.tasks.length > 0) {
        // Filter tasks that have videos generated
        const completedTasks = data.data.tasks.filter(task => task.videos && task.videos.length > 0);
        
        if (completedTasks.length === 0) {
          videoList.innerHTML = '<div class="loading">No completed videos found.</div>';
          return;
        }
        
        completedTasks.forEach(task => {
          const item = document.createElement('div');
          item.className = 'video-item';
          
          const title = task.params && task.params.video_subject ? task.params.video_subject : 'Untitled Video';
          const videoPath = task.videos[0]; 
          const videoUrl = `${API_URL}/download/${videoPath}`;
          const isUploaded = uploadedTasks.includes(task.task_id);
          
          if (isUploaded) {
            item.innerHTML = `
              <div class="video-title">${title} <span style="color: #00f2fe; font-size: 12px;">✓ Uploaded</span></div>
              <div class="video-meta">ID: ${task.task_id.substring(0, 8)}...</div>
              <div class="btn-group">
                <button class="btn" disabled style="background-color: #333; color: #888; flex: 1;">Already Uploaded</button>
                <button class="btn delete-btn" data-taskid="${task.task_id}">Delete</button>
              </div>
            `;
          } else {
            item.innerHTML = `
              <div class="video-title">${title}</div>
              <div class="video-meta">ID: ${task.task_id.substring(0, 8)}...</div>
              <div class="btn-group">
                <button class="btn upload-btn" data-url="${videoUrl}" data-title="${title}" data-taskid="${task.task_id}" style="flex: 1;">Upload to TikTok</button>
                <button class="btn delete-btn" data-taskid="${task.task_id}">Delete</button>
              </div>
            `;
          }
          
          videoList.appendChild(item);
        });
        
        // Add event listeners to buttons
        document.querySelectorAll('.upload-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const url = e.target.getAttribute('data-url');
            const title = e.target.getAttribute('data-title');
            const taskId = e.target.getAttribute('data-taskid');
            initiateUpload(url, title, taskId, e.target);
          });
        });
        
        document.querySelectorAll('.delete-btn').forEach(btn => {
          btn.addEventListener('click', async (e) => {
            const taskId = e.target.getAttribute('data-taskid');
            const itemElement = e.target.closest('.video-item');
            
            if (confirm("Are you sure you want to permanently delete this generated video?")) {
              e.target.disabled = true;
              e.target.innerText = '...';
              try {
                const res = await fetch(`${API_URL}/tasks/${taskId}`, { method: 'DELETE' });
                if (res.ok) {
                  itemElement.remove();
                  if (document.querySelectorAll('.video-item').length === 0) {
                     videoList.innerHTML = '<div class="loading">No completed videos found.</div>';
                  }
                } else {
                  alert("Failed to delete video from server.");
                  e.target.disabled = false;
                  e.target.innerText = 'Delete';
                }
              } catch (err) {
                alert("Error connecting to server.");
                e.target.disabled = false;
                e.target.innerText = 'Delete';
              }
            }
          });
        });
        
      } else {
        videoList.innerHTML = '<div class="loading">No videos found. Generate some in MoneyPrinterTurbo first!</div>';
      }
    });
  } catch (err) {
    console.error(err);
    loading.innerHTML = `Error connecting to MoneyPrinterTurbo API.<br><br>Make sure the backend is running on port 8080.`;
    loading.style.color = '#ff4444';
  }
}

function initiateUpload(videoUrl, title, taskId, button) {
  const statusEl = document.getElementById('status');
  button.disabled = true;
  button.innerText = 'Sending to TikTok...';
  statusEl.innerText = 'Opening TikTok upload page...';
  
  // Send message to background script to orchestrate the upload
  chrome.runtime.sendMessage({
    action: "START_TIKTOK_UPLOAD",
    payload: {
      taskId: taskId,
      videoUrl: videoUrl,
      title: title
    }
  }, (response) => {
    if (chrome.runtime.lastError) {
      statusEl.innerText = 'Error: ' + chrome.runtime.lastError.message;
      button.disabled = false;
      button.innerText = 'Upload to TikTok';
    } else {
      statusEl.innerText = 'TikTok tab opened. Switch to it to continue.';
      setTimeout(() => {
          button.disabled = false;
          button.innerText = 'Upload to TikTok';
          statusEl.innerText = '';
      }, 3000);
    }
  });
}
