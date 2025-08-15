let currentUser = null;

// Immediately clear staff sessions when page loads (before checking auth)
document.addEventListener("DOMContentLoaded", function () {
  // Clear staff sessions aggressively on page load
  clearStaffSession();
  // Wait a moment then check auth status
  setTimeout(checkAuthStatus, 500);
});

// Also clear on page visibility change (when user returns to tab)
// But only if we're not in the middle of a login process
document.addEventListener("visibilitychange", function () {
  if (!document.hidden && !isLoggingIn) {
    clearStaffSession();
    setTimeout(checkAuthStatus, 200);
  }
});

// Flag to track if we're in the middle of logging in
let isLoggingIn = false;

function switchAuthTab(tab) {
  // Update tab buttons
  document
    .querySelectorAll(".auth-tab")
    .forEach((t) => t.classList.remove("active"));
  event.target.classList.add("active");

  // Update forms
  document
    .querySelectorAll(".auth-form")
    .forEach((f) => f.classList.remove("active"));
  document.getElementById(tab + "Form").classList.add("active");
}

function showAlert(message, type, container = "auth") {
  const alertId =
    container +
    (type === "error" ? "Error" : type === "success" ? "Success" : "Info");
  const alert = document.getElementById(alertId);
  alert.textContent = message;
  alert.style.display = "block";

  setTimeout(() => {
    alert.style.display = "none";
  }, 5000);
}

function checkAuthStatus() {
  // Automatically clear any staff session when accessing user interface
  clearStaffSession();

  // Check user session with server
  fetch("/user-auth-status", {
    credentials: "include", // Include cookies for session management
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.logged_in) {
        currentUser = { email: data.email };
        showUserLoggedIn();
        // Hide any auth warnings since we've cleared conflicts
        hideAuthWarning();
      } else {
        // Clear local storage if server session is invalid
        localStorage.removeItem("currentUser");
        hideAuthWarning();
      }
    })
    .catch(() => {
      // Fallback to localStorage for demo
      const savedUser = localStorage.getItem("currentUser");
      if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showUserLoggedIn();
      }
      hideAuthWarning();
    });
}

function checkConflictingSessions() {
  // Check if staff is logged in
  fetch("/admin-dashboard")
    .then((response) => {
      if (response.ok) {
        showAuthWarning(
          "⚠️ Staff session detected. You are currently logged in as admin staff."
        );
      }
    })
    .catch(() => {});
}

function showAuthWarning(message) {
  document.getElementById("statusText").textContent = message;
  document.getElementById("authStatusBar").classList.add("show");
}

function clearAllSessions() {
  // Clear all sessions and localStorage
  localStorage.clear();
  fetch("/clear-all-sessions", {
    method: "POST",
    credentials: "include",
  })
    .then(() => {
      // Instead of reloading, just reset the UI state
      currentUser = null;
      document.getElementById("authContainer").style.display = "block";
      document.getElementById("userStatus").classList.remove("show");
      document.getElementById("loanApplicationSection").style.display = "none";
      hideAuthWarning();
      // Clear form data
      document.getElementById("loanApplicationForm").reset();
    })
    .catch(() => {
      // Only reload as fallback if there's an error
      location.reload();
    });
}

function clearStaffSession() {
  // Clear staff session when user logs in - more aggressive approach
  Promise.all([
    fetch("/clear-staff-session", {
      method: "POST",
      credentials: "include",
    }).catch(() => {}),
    fetch("/admin-logout", {
      method: "POST",
      credentials: "include",
    }).catch(() => {}),
    fetch("/logout", {
      method: "POST",
      credentials: "include",
    }).catch(() => {}),
  ]).then(() => {
    // Force clear any staff-related localStorage
    Object.keys(localStorage).forEach((key) => {
      if (key.includes("staff") || key.includes("admin")) {
        localStorage.removeItem(key);
      }
    });
  });
}

function hideAuthWarning() {
  document.getElementById("authStatusBar").classList.remove("show");
}

function refreshSession() {
  // Attempt to refresh the session
  return fetch("/user-auth-status", {
    credentials: "include"
  })
  .then(response => response.json())
  .then(data => {
    if (data.logged_in) {
      currentUser = { email: data.email };
      return true;
    } else {
      return false;
    }
  })
  .catch(() => false);
}

function showUserLoggedIn() {
  document.getElementById("authContainer").style.display = "none";
  document.getElementById("userStatus").classList.add("show");
  document.getElementById("userEmail").textContent = currentUser.email;
  document.getElementById("loanApplicationSection").style.display = "block";

  // Load user data when logged in
  loadDrafts();
  loadHistory();
}

function switchAppTab(tabName) {
  // Remove active class from all tabs
  document
    .querySelectorAll(".app-tab")
    .forEach((tab) => tab.classList.remove("active"));
  document
    .querySelectorAll(".tab-content")
    .forEach((content) => content.classList.remove("active"));

  // Add active class to selected tab
  event.target.classList.add("active");
  document.getElementById(tabName + "Tab").classList.add("active");

  // Load data for specific tabs
  if (tabName === "drafts") {
    loadDraftsFromServer(); // Use the new server-side function
  } else if (tabName === "history") {
    loadHistory();
  }
}

function loadDrafts() {
  const draftsContainer = document.getElementById("draftsContainer");
  const drafts = JSON.parse(localStorage.getItem("applicationDrafts") || "[]");
  const userDrafts = drafts.filter(
    (draft) => draft.userEmail === currentUser.email
  );

  if (userDrafts.length === 0) {
    draftsContainer.innerHTML = `
                    <div class="empty-state">
                        <div style="text-align: center; padding: 3rem; color: #6c757d;">
                            <div style="font-size: 4rem; margin-bottom: 1rem;">💾</div>
                            <h4>No Drafts Found</h4>
                            <p>Pre-approved applications will appear here for document upload.</p>
                            <button onclick="switchAppTab('newApplication')" class="btn-primary" style="margin-top: 1rem; width: auto; padding: 0.8rem 2rem;">
                                Create New Application
                            </button>
                        </div>
                    </div>
                `;
    return;
  }

  let draftsHTML = "";
  userDrafts.forEach((draft) => {
    const statusClass = getStatusClass(draft.status);
    const formattedDate = new Date(draft.savedAt).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

    draftsHTML += `
                    <div class="application-card">
                        <div class="application-header">
                            <div class="application-id">📋 ${
                              draft.applicationId
                            }</div>
                            <div class="status-badge ${statusClass}">${draft.status.replace(
      "_",
      " "
    )}</div>
                        </div>
                        
                        <div class="application-details">
                            <div class="detail-item">
                                <div class="detail-label">Loan Type</div>
                                <div class="detail-value">${
                                  draft.formData["loan-type"]
                                }</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Amount</div>
                                <div class="detail-value">₹${parseInt(
                                  draft.formData["loan-amount"]
                                ).toLocaleString()}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Saved On</div>
                                <div class="detail-value">${formattedDate}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Status</div>
                                <div class="detail-value">${
                                  draft.status === "APPROVED"
                                    ? "Ready for Documents"
                                    : "Conditional Approval"
                                }</div>
                            </div>
                        </div>
                        
                        <div class="application-actions">
                            <button onclick="uploadDocumentsForDraft('${
                              draft.applicationId
                            }', '${
      draft.requiredDocuments
    }')" class="btn-small btn-upload">
                                📎 Upload Documents
                            </button>
                            <button onclick="viewDraftDetails('${
                              draft.applicationId
                            }')" class="btn-small btn-view">
                                👁️ View Details
                            </button>
                        </div>
                    </div>
                `;
  });

  draftsContainer.innerHTML = draftsHTML;
}

function loadHistory() {
  const historyContainer = document.getElementById("historyContainer");

  // Get applications from server
  fetch("/user-applications", {
    credentials: "include", // Include cookies for session management
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success && data.applications.length > 0) {
        let historyHTML = "";
        data.applications.forEach((app) => {
          const statusClass = getStatusClass(
            app.status || app.eligibility_status
          );
          const formattedDate = new Date(app.created_at).toLocaleDateString(
            "en-US",
            {
              year: "numeric",
              month: "short",
              day: "numeric",
            }
          );

          historyHTML += `
                                <div class="application-card">
                                    <div class="application-header">
                                        <div class="application-id">📋 ${
                                          app.application_id
                                        }</div>
                                        <div class="status-badge ${statusClass}">${(
            app.status || app.eligibility_status
          ).replace("_", " ")}</div>
                                    </div>
                                    
                                    <div class="application-details">
                                        <div class="detail-item">
                                            <div class="detail-label">Loan Type</div>
                                            <div class="detail-value">${
                                              app.loan_type
                                            }</div>
                                        </div>
                                        <div class="detail-item">
                                            <div class="detail-label">Amount</div>
                                            <div class="detail-value">₹${parseInt(
                                              app.loan_amount
                                            ).toLocaleString()}</div>
                                        </div>
                                        <div class="detail-item">
                                            <div class="detail-label">Applied On</div>
                                            <div class="detail-value">${formattedDate}</div>
                                        </div>
                                        <div class="detail-item">
                                            <div class="detail-label">Current Status</div>
                                            <div class="detail-value">${getStatusText(
                                              app.status ||
                                                app.eligibility_status
                                            )}</div>
                                        </div>
                                    </div>
                                    
                                    <div class="application-actions">
                                        <button onclick="viewApplicationDetails('${
                                          app.application_id
                                        }')" class="btn-small btn-view">
                                            👁️ View Details
                                        </button>
                                        ${
                                          (app.status === "APPROVED" ||
                                            app.status ===
                                              "CONDITIONALLY_APPROVED" ||
                                            app.eligibility_status ===
                                              "APPROVED" ||
                                            app.eligibility_status ===
                                              "CONDITIONALLY_APPROVED") &&
                                          app.status !== "OBJECTION_RAISED"
                                            ? `<button onclick="uploadDocumentsForApplication('${app.application_id}')" class="btn-small btn-upload">📎 Upload Documents</button>`
                                            : ""
                                        }
                                    </div>
                                </div>
                            `;
        });

        historyContainer.innerHTML = historyHTML;
      } else {
        historyContainer.innerHTML = `
                            <div class="empty-state">
                                <div style="text-align: center; padding: 3rem; color: #6c757d;">
                                    <div style="font-size: 4rem; margin-bottom: 1rem;">📈</div>
                                    <h4>No Applications Found</h4>
                                    <p>Your submitted loan applications will appear here.</p>
                                    <button onclick="switchAppTab('newApplication')" class="btn-primary" style="margin-top: 1rem; width: auto; padding: 0.8rem 2rem;">
                                        Apply for Your First Loan
                                    </button>
                                </div>
                            </div>
                        `;
      }
    })
    .catch((error) => {
      console.error("Error loading history:", error);
      historyContainer.innerHTML = `
                        <div class="empty-state">
                            <div style="text-align: center; padding: 3rem; color: #dc2626;">
                                <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
                                <h4>Error Loading History</h4>
                                <p>Unable to fetch your application history. Please try again.</p>
                                <button onclick="loadHistory()" class="btn-primary" style="margin-top: 1rem; width: auto; padding: 0.8rem 2rem;">
                                    Retry
                                </button>
                            </div>
                        </div>
                    `;
    });
}

function getStatusClass(status) {
  switch (status?.toLowerCase()) {
    case "approved":
      return "status-approved";
    case "conditionally_approved":
      return "status-conditional";
    case "rejected":
      return "status-rejected";
    case "objection_raised":
      return "status-objection";
    default:
      return "status-pending";
  }
}

function getStatusText(status) {
  switch (status?.toLowerCase()) {
    case "approved":
      return "Approved - Upload Documents";
    case "conditionally_approved":
      return "Conditional Approval";
    case "rejected":
      return "Not Approved";
    case "pending":
      return "Under Review";
    case "objection_raised":
      return "Action Required - See Drafts";
    default:
      return "Processing";
  }
}

function uploadDocumentsForDraft(applicationId, requiredDocs) {
  // Switch to new application tab and show upload section
  switchAppTab("newApplication");
  setTimeout(() => {
    showDocumentUploadSection(applicationId, requiredDocs);
    document
      .getElementById("newApplicationTab")
      .scrollIntoView({ behavior: "smooth" });
  }, 100);
}

function uploadDocumentsForApplication(applicationId) {
  // Get application details and show upload section
  fetch(`/application-details/${applicationId}`, {
    credentials: "include", // Include cookies for session management
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const requiredDocs =
          data.application.required_documents ||
          "Identity Proof, Income Proof, Address Proof";
        uploadDocumentsForDraft(applicationId, requiredDocs);
      }
    })
    .catch((error) => {
      console.error("Error getting application details:", error);
      showAlert("Error loading application details", "error", "application");
    });
}

function viewDraftDetails(applicationId) {
  const drafts = JSON.parse(localStorage.getItem("applicationDrafts") || "[]");
  const draft = drafts.find((d) => d.applicationId === applicationId);

  if (draft) {
    alert(`Application Details for ${applicationId}:
                
Loan Type: ${draft.formData["loan-type"]}
Amount: ₹${parseInt(draft.formData["loan-amount"]).toLocaleString()}
Status: ${draft.status}
Required Documents: ${draft.requiredDocuments}
Saved: ${new Date(draft.savedAt).toLocaleString()}`);
  }
}

function viewApplicationDetails(applicationId) {
  // Fetch and display application details
  fetch(`/application-details/${applicationId}`, {
    credentials: "include", // Include cookies for session management
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const app = data.application;
        alert(`Application Details for ${applicationId}:
                        
Applicant: ${app.full_name}
Loan Type: ${app.loan_type}
Amount: ₹${parseInt(app.loan_amount).toLocaleString()}
Status: ${app.eligibility_status}
Applied: ${new Date(app.created_at).toLocaleString()}
Required Documents: ${app.required_documents || "N/A"}`);
      }
    })
    .catch((error) => {
      console.error("Error loading application details:", error);
      showAlert("Error loading application details", "error", "application");
    });
}

function logout() {
  currentUser = null;
  localStorage.removeItem("currentUser");
  document.getElementById("authContainer").style.display = "block";
  document.getElementById("userStatus").classList.remove("show");
  document.getElementById("loanApplicationSection").style.display = "none";
}

// Login Form Handler
document
  .getElementById("loginForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    isLoggingIn = true; // Set flag to prevent interference
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;

    try {
      const response = await fetch("/user-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Include cookies for session management
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (data.success) {
        // Clear staff session when user logs in
        clearStaffSession();

        currentUser = { email: email };
        localStorage.setItem("currentUser", JSON.stringify(currentUser));
        showAlert("Login successful!", "success");
        setTimeout(() => {
          showUserLoggedIn();
          isLoggingIn = false; // Clear flag after successful login
        }, 1000);
      } else {
        showAlert(data.error || "Login failed", "error");
        isLoggingIn = false; // Clear flag on failed login
      }
    } catch (error) {
      showAlert("Network error. Please try again.", "error");
      isLoggingIn = false; // Clear flag on error
    }
  });

// Register Form Handler
document
  .getElementById("registerForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    isLoggingIn = true; // Set flag to prevent interference
    const fullName = document.getElementById("regFullName").value;
    const email = document.getElementById("regEmail").value;
    const phone = document.getElementById("regPhone").value;
    const password = document.getElementById("regPassword").value;

    try {
      const response = await fetch("/user-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include", // Include cookies for session management
        body: JSON.stringify({ fullName, email, phone, password }),
      });

      const data = await response.json();

      if (data.success) {
        // Clear staff session when user registers
        clearStaffSession();

        currentUser = { email: email };
        localStorage.setItem("currentUser", JSON.stringify(currentUser));
        showAlert("Registration successful!", "success");
        setTimeout(() => {
          showUserLoggedIn();
          isLoggingIn = false; // Clear flag after successful registration
        }, 1000);
      } else {
        showAlert(data.error || "Registration failed", "error");
        isLoggingIn = false; // Clear flag on failed registration
      }
    } catch (error) {
      showAlert("Network error. Please try again.", "error");
      isLoggingIn = false; // Clear flag on error
    }
  });

// Loan Application Form Handler
document
  .getElementById("loanApplicationForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const submitBtn = document.getElementById("submitApplicationBtn");
    submitBtn.disabled = true;
    submitBtn.textContent = "🔄 Processing Application with Watson AI...";

    // Validate authentication before submitting
    try {
      const authCheck = await fetch("/user-auth-status", {
        credentials: "include"
      });
      const authData = await authCheck.json();
      
      if (!authData.logged_in) {
        showAlert("⚠️ Session expired. Please login again to submit your application.", "error", "application");
        logout(); // Force logout and show login form
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit Application";
        return;
      }
    } catch (error) {
      showAlert("⚠️ Unable to verify authentication. Please login again.", "error", "application");
      logout();
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Application";
      return;
    }

    // Get current language
    const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';

    const formData = {
      "full-name": document.getElementById("fullName").value,
      "date-of-birth": document.getElementById("dateOfBirth").value,
      gender: document.getElementById("gender").value,
      "marital-status": document.getElementById("maritalStatus").value,
      nationality: document.getElementById("nationality").value,
      "contact-number": document.getElementById("contactNumber").value,
      "employment-type": document.getElementById("employmentType").value,
      "employer-name": document.getElementById("employerName").value,
      "annual-income": document.getElementById("annualIncome").value,
      "existing-loans":
        document.getElementById("existingLoans").value || "None",
      "loan-type": document.getElementById("loanType").value,
      "loan-amount": document.getElementById("loanAmount").value,
      "loan-tenure": document.getElementById("loanTenure").value,
      "loan-purpose": document.getElementById("loanPurpose").value,
      "preferred-emi": document.getElementById("preferredEmi").value || "",
      "cibil-score": document.getElementById("cibilScore").value,
      "language": currentLanguage
    };

    try {
      const response = await fetch("/evaluate-loan-eligibility", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.success) {
        // Show AI assessment popup
        showLoanAssessmentPopup(data, formData);
      } else {
        // Check if it's an authentication error
        if (data.error === 'Not authenticated') {
          showAlert("🔒 Session expired. Please login again to continue.", "error", "application");
          logout(); // Force logout and show login form
        } else {
          showAlert(data.error || "Application processing failed", "error", "application");
        }
      }
    } catch (error) {
      showAlert("⚠️ Network error. Please check your connection and try again.", "error", "application");
    } finally {
      // Reset button
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Application";
    }
  });

// Show Loan Assessment Popup with AI results
function showLoanAssessmentPopup(assessmentData, formData) {
  const popup = document.createElement('div');
  popup.className = 'assessment-popup-overlay';
  popup.innerHTML = createAssessmentPopupContent(assessmentData, formData);
  document.body.appendChild(popup);
  
  // Add event listeners for popup interactions
  setupAssessmentPopupEvents(popup, assessmentData, formData);
}

function createAssessmentPopupContent(data, formData) {
  const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
  
  if (data.eligible) {
    // Eligible - Show schemes
    return `
      <div class="assessment-popup">
        <div class="popup-header">
          <h2>🎉 ${getTranslation('loan-eligible-title', currentLanguage)}</h2>
          <button class="close-popup" onclick="closeAssessmentPopup()">&times;</button>
        </div>
        
        <div class="popup-content">
          <div class="ai-assessment">
            <h3>🤖 ${getTranslation('ai-assessment', currentLanguage)}</h3>
            <div class="assessment-text">${data.ai_assessment}</div>
          </div>
          
          <div class="recommended-schemes">
            <h3>📋 ${getTranslation('recommended-schemes', currentLanguage)}</h3>
            <div class="schemes-grid">
              ${data.recommended_schemes.map(scheme => createSchemeCard(scheme, currentLanguage)).join('')}
            </div>
          </div>
          
          <div class="popup-actions">
            <button class="btn-secondary" onclick="askLoanAgent()">
              💬 ${getTranslation('ask-loan-agent', currentLanguage)}
            </button>
            <button class="btn-secondary" onclick="selectNoneScheme()">
              ❌ ${getTranslation('none-scheme', currentLanguage)}
            </button>
          </div>
        </div>
      </div>
    `;
  } else {
    // Not eligible - Show improvement suggestions
    return `
      <div class="assessment-popup">
        <div class="popup-header">
          <h2>📋 ${getTranslation('loan-assessment-title', currentLanguage)}</h2>
          <button class="close-popup" onclick="closeAssessmentPopup()">&times;</button>
        </div>
        
        <div class="popup-content">
          <div class="ai-assessment">
            <h3>🤖 ${getTranslation('ai-assessment', currentLanguage)}</h3>
            <div class="assessment-text">${data.ai_assessment}</div>
          </div>
          
          <div class="improvement-suggestions">
            <h3>🔧 ${getTranslation('improvement-suggestions', currentLanguage)}</h3>
            <ul class="suggestions-list">
              ${data.improvement_suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
            </ul>
          </div>
          
          <div class="popup-actions">
            <button class="btn-secondary" onclick="askLoanAgent()">
              💬 ${getTranslation('ask-loan-agent', currentLanguage)}
            </button>
            <button class="btn-primary" onclick="closeAssessmentPopup()">
              ✅ ${getTranslation('understand', currentLanguage)}
            </button>
          </div>
        </div>
      </div>
    `;
  }
}

function createSchemeCard(schemeData, language) {
  const scheme = schemeData.scheme_data;
  return `
    <div class="scheme-card" data-scheme-id="${schemeData.scheme_id}">
      <div class="scheme-header">
        <h4>${scheme.name}</h4>
        <div class="match-score">Match: ${schemeData.match_score}%</div>
      </div>
      <div class="scheme-details">
        <p><strong>Interest Rate:</strong> ${scheme.interest_rate}</p>
        <p><strong>Max Tenure:</strong> ${scheme.max_tenure} years</p>
        <p><strong>Amount:</strong> ₹${scheme.min_amount.toLocaleString()} - ₹${scheme.max_amount.toLocaleString()}</p>
        <p><strong>Min Income:</strong> ₹${scheme.min_income.toLocaleString()}</p>
      </div>
      <div class="scheme-features">
        <h5>Key Features:</h5>
        <ul>
          ${scheme.features.slice(0, 2).map(feature => `<li>${feature}</li>`).join('')}
        </ul>
      </div>
      <div class="scheme-actions">
        <button class="btn-primary btn-small" onclick="selectScheme('${schemeData.scheme_id}')">
          Select This Scheme
        </button>
        <button class="btn-secondary btn-small" onclick="viewSchemeDetails('${schemeData.scheme_id}')">
          View Details
        </button>
      </div>
    </div>
  `;
}

function setupAssessmentPopupEvents(popup, assessmentData, formData) {
  // Store data for later use
  window.currentAssessmentData = assessmentData;
  window.currentFormData = formData;
  
  // Close popup when clicking outside
  popup.addEventListener('click', function(e) {
    if (e.target === popup) {
      closeAssessmentPopup();
    }
  });
}

// Popup Action Functions
function closeAssessmentPopup() {
  const popup = document.querySelector('.assessment-popup-overlay');
  if (popup) {
    popup.remove();
  }
}

function selectScheme(schemeId) {
  const schemeData = window.currentAssessmentData.recommended_schemes.find(s => s.scheme_id === schemeId);
  if (schemeData) {
    showSchemeApplicationFlow(schemeData);
  }
}

function viewSchemeDetails(schemeId) {
  const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
  
  // Call backend to get detailed scheme information
  fetch('/get-scheme-details', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ 
      scheme_id: schemeId,
      language: currentLanguage 
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showSchemeDetailsPopup(data.scheme, data.ai_explanation);
    } else {
      alert('Error loading scheme details');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Network error loading scheme details');
  });
}

function showSchemeDetailsPopup(scheme, aiExplanation) {
  const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
  
  const popup = document.createElement('div');
  popup.className = 'scheme-details-popup-overlay';
  popup.innerHTML = `
    <div class="scheme-details-popup">
      <div class="popup-header">
        <h2>${scheme.name} - Details</h2>
        <button class="close-popup" onclick="closeSchemeDetailsPopup()">&times;</button>
      </div>
      
      <div class="popup-content">
        <div class="scheme-info">
          <div class="info-grid">
            <div class="info-item">
              <strong>Type:</strong> ${scheme.type}
            </div>
            <div class="info-item">
              <strong>Interest Rate:</strong> ${scheme.interest_rate}
            </div>
            <div class="info-item">
              <strong>Loan Amount:</strong> ₹${scheme.min_amount.toLocaleString()} - ₹${scheme.max_amount.toLocaleString()}
            </div>
            <div class="info-item">
              <strong>Max Tenure:</strong> ${scheme.max_tenure} years
            </div>
            <div class="info-item">
              <strong>Min Income:</strong> ₹${scheme.min_income.toLocaleString()}
            </div>
            <div class="info-item">
              <strong>Min CIBIL Score:</strong> ${scheme.eligibility.cibil_score}
            </div>
          </div>
          
          <div class="eligibility-criteria">
            <h4>Eligibility Criteria:</h4>
            <ul>
              <li>Age: ${scheme.eligibility.min_age} - ${scheme.eligibility.max_age} years</li>
              <li>Employment: ${scheme.eligibility.employment.join(', ')}</li>
              <li>CIBIL Score: ${scheme.eligibility.cibil_score}+</li>
            </ul>
          </div>
          
          <div class="required-documents">
            <h4>Required Documents:</h4>
            <ul>
              ${scheme.documents.map(doc => `<li>${doc}</li>`).join('')}
            </ul>
          </div>
          
          <div class="scheme-features">
            <h4>Key Features:</h4>
            <ul>
              ${scheme.features.map(feature => `<li>${feature}</li>`).join('')}
            </ul>
          </div>
          
          <div class="ai-explanation">
            <h4>🤖 AI Expert Analysis:</h4>
            <div class="explanation-text">${aiExplanation}</div>
          </div>
        </div>
        
        <div class="popup-actions">
          <button class="btn-primary" onclick="selectSchemeFromDetails('${scheme.name}')">
            ✅ Continue with this Scheme
          </button>
          <button class="btn-secondary" onclick="closeSchemeDetailsPopup()">
            🔙 Back to Options
          </button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
}

function closeSchemeDetailsPopup() {
  const popup = document.querySelector('.scheme-details-popup-overlay');
  if (popup) {
    popup.remove();
  }
}

function selectSchemeFromDetails(schemeName) {
  closeSchemeDetailsPopup();
  // Find the scheme by name and proceed
  const schemeData = window.currentAssessmentData.recommended_schemes.find(s => s.scheme_data.name === schemeName);
  if (schemeData) {
    showSchemeApplicationFlow(schemeData);
  }
}

function showSchemeApplicationFlow(schemeData) {
  closeAssessmentPopup();
  
  const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
  
  // Submit the application with selected scheme
  fetch('/submit-scheme-application', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      scheme_id: schemeData.scheme_id,
      application_data: window.currentFormData
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Show document upload section
      showSchemeDocumentUpload(data.application_id, data.scheme, data.required_documents);
    } else {
      showAlert(data.error || 'Error submitting scheme application', 'error', 'application');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showAlert('Network error submitting application', 'error', 'application');
  });
}

function showSchemeDocumentUpload(applicationId, scheme, requiredDocuments) {
  const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
  
  const popup = document.createElement('div');
  popup.className = 'document-upload-popup-overlay';
  popup.innerHTML = `
    <div class="document-upload-popup">
      <div class="popup-header">
        <h2>📄 Document Upload - ${scheme.name}</h2>
        <div class="application-id">Application ID: ${applicationId}</div>
      </div>
      
      <div class="popup-content">
        <div class="success-message">
          <h3>🎉 Application Submitted Successfully!</h3>
          <p>Your application for <strong>${scheme.name}</strong> has been submitted.</p>
          <p>Please upload the required documents to complete your application.</p>
        </div>
        
        <div class="document-requirements">
          <h4>Required Documents:</h4>
          <div class="documents-grid">
            ${requiredDocuments.map(doc => `
              <div class="document-item">
                <div class="document-name">${doc}</div>
                <div class="upload-section">
                  <input type="file" id="file-${doc.replace(/\s+/g, '-')}" accept=".pdf,.jpg,.jpeg,.png" />
                  <button class="btn-upload" onclick="uploadDocument('${applicationId}', '${doc}')">
                    📤 Upload
                  </button>
                </div>
                <div class="upload-status" id="status-${doc.replace(/\s+/g, '-')}"></div>
              </div>
            `).join('')}
          </div>
        </div>
        
        <div class="popup-actions">
          <button class="btn-primary" onclick="completeDocumentUpload('${applicationId}')">
            ✅ Complete Application
          </button>
          <button class="btn-secondary" onclick="closeDocumentUploadPopup()">
            📋 Upload Later
          </button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
}

function uploadDocument(applicationId, documentType) {
  const fileId = `file-${documentType.replace(/\s+/g, '-')}`;
  const statusId = `status-${documentType.replace(/\s+/g, '-')}`;
  const fileInput = document.getElementById(fileId);
  const statusDiv = document.getElementById(statusId);
  
  if (!fileInput.files[0]) {
    statusDiv.innerHTML = '<span class="error">Please select a file</span>';
    return;
  }
  
  const formData = new FormData();
  formData.append('application_id', applicationId);
  formData.append('document_type', documentType);
  formData.append('document', fileInput.files[0]);
  
  statusDiv.innerHTML = '<span class="uploading">📤 Uploading...</span>';
  
  fetch('/upload-documents', {
    method: 'POST',
    credentials: 'include',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      statusDiv.innerHTML = '<span class="success">✅ Uploaded</span>';
    } else {
      statusDiv.innerHTML = `<span class="error">❌ ${data.error}</span>`;
    }
  })
  .catch(error => {
    console.error('Upload error:', error);
    statusDiv.innerHTML = '<span class="error">❌ Upload failed</span>';
  });
}

function completeDocumentUpload(applicationId) {
  closeDocumentUploadPopup();
  showAlert(`Application ${applicationId} completed! Our team will review your documents and contact you soon.`, 'success', 'application');
  
  // Reset form
  document.getElementById("loanApplicationForm").reset();
}

function closeDocumentUploadPopup() {
  const popup = document.querySelector('.document-upload-popup-overlay');
  if (popup) {
    popup.remove();
  }
}

function askLoanAgent() {
  // Don't close assessment popup, transform it into chat interface
  const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
  
  // Get the existing popup
  const popup = document.querySelector('.assessment-popup-overlay');
  if (!popup) return;
  
  // Replace popup content with chat interface
  const assessmentPopup = popup.querySelector('.assessment-popup');
  assessmentPopup.innerHTML = `
    <div class="popup-header">
      <h2>💬 ${getTranslation('chat-with-agent', currentLanguage)}</h2>
      <button class="close-popup" onclick="closeAssessmentPopup()">&times;</button>
    </div>
    
    <div class="popup-content">
      <div class="chat-container-popup">
        <div class="chat-messages-popup" id="chatMessagesPopup">
          <div class="message bot-message">
            ${getTranslation('agent-welcome', currentLanguage)}
          </div>
        </div>
        
        <div class="quick-actions-popup">
          <div class="quick-action-popup" onclick="sendQuickMessagePopup('${getTranslation('quick-loan-types-msg', currentLanguage)}')">${getTranslation('quick-loan-types', currentLanguage)}</div>
          <div class="quick-action-popup" onclick="sendQuickMessagePopup('${getTranslation('quick-eligibility-msg', currentLanguage)}')">${getTranslation('quick-eligibility', currentLanguage)}</div>
          <div class="quick-action-popup" onclick="sendQuickMessagePopup('${getTranslation('quick-documents-msg', currentLanguage)}')">${getTranslation('quick-documents', currentLanguage)}</div>
        </div>
        
        <div class="chat-input-popup">
          <input type="text" id="messageInputPopup" placeholder="${getTranslation('chat-placeholder', currentLanguage)}" onkeypress="handleKeyPressPopup(event)">
          <button class="send-btn-popup" onclick="sendMessagePopup()" id="sendBtnPopup">${getTranslation('send-btn', currentLanguage)}</button>
        </div>
        
        <div class="typing-indicator-popup" id="typingIndicatorPopup" style="display: none;">
          <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
          </div>
        </div>
        
        <div class="popup-actions" style="margin-top: 1rem;">
          <button class="btn-secondary" onclick="goBackToAssessment()">
            ← ${getTranslation('back-to-assessment', currentLanguage)}
          </button>
        </div>
      </div>
    </div>
  `;
  
  // Store original assessment data for going back
  window.originalAssessmentData = window.currentAssessmentData;
  window.originalFormData = window.currentFormData;
}

function selectNoneScheme() {
  closeAssessmentPopup();
  showAlert('You can apply again anytime or chat with our LoanAgent for personalized assistance.', 'info', 'application');
}

// Chat functions for popup
function handleKeyPressPopup(event) {
  if (event.key === "Enter") {
    sendMessagePopup();
  }
}

function sendQuickMessagePopup(message) {
  document.getElementById('messageInputPopup').value = message;
  sendMessagePopup();
}

async function sendMessagePopup() {
  const messageInput = document.getElementById('messageInputPopup');
  const sendBtn = document.getElementById('sendBtnPopup');
  const message = messageInput.value.trim();
  
  if (!message) return;

  // Add user message
  addMessagePopup(message, "user");
  messageInput.value = "";

  // Disable send button and show typing
  sendBtn.disabled = true;
  showTypingPopup();

  try {
    // Get current language from localStorage
    const currentLanguage = localStorage.getItem('selectedLanguage') || 'en';
    
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        query: message,
        language: currentLanguage
      }),
    });

    const data = await response.json();

    // Hide typing and add bot response
    hideTypingPopup();
    addMessagePopup(
      data.response || data.error || "Sorry, I encountered an error.",
      "bot"
    );
  } catch (error) {
    hideTypingPopup();
    addMessagePopup(
      "Sorry, I'm having trouble connecting. Please try again.",
      "bot"
    );
  }

  sendBtn.disabled = false;
}

function addMessagePopup(message, type) {
  const chatMessages = document.getElementById("chatMessagesPopup");
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}-message`;
  messageDiv.textContent = message;

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingPopup() {
  const typingIndicator = document.getElementById("typingIndicatorPopup");
  const chatMessages = document.getElementById("chatMessagesPopup");
  typingIndicator.style.display = "block";
  chatMessages.appendChild(typingIndicator);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingPopup() {
  const typingIndicator = document.getElementById("typingIndicatorPopup");
  typingIndicator.style.display = "none";
}

function goBackToAssessment() {
  // Restore original assessment popup
  if (window.originalAssessmentData && window.originalFormData) {
    const popup = document.querySelector('.assessment-popup-overlay');
    if (popup) {
      const assessmentPopup = popup.querySelector('.assessment-popup');
      assessmentPopup.innerHTML = createAssessmentPopupContent(window.originalAssessmentData, window.originalFormData);
      
      // Re-setup event listeners
      setupAssessmentPopupEvents(popup, window.originalAssessmentData, window.originalFormData);
    }
  }
}

// Translation helper function
function getTranslation(key, language) {
  const translations = {
    'en': {
      'loan-eligible-title': 'Congratulations! You are Eligible',
      'loan-assessment-title': 'Loan Assessment Results',
      'ai-assessment': 'AI Assessment',
      'recommended-schemes': 'Recommended Loan Schemes',
      'improvement-suggestions': 'Improvement Suggestions',
      'ask-loan-agent': 'Ask LoanAgent',
      'none-scheme': 'None of These',
      'understand': 'I Understand',
      'chat-with-agent': 'Chat with LoanAgent',
      'agent-welcome': 'Hello! I\'m your AI LoanAgent. I can help you with loan information, eligibility questions, and guidance on improving your application. How can I assist you?',
      'quick-loan-types': 'Loan Types',
      'quick-eligibility': 'Eligibility Help',
      'quick-documents': 'Documents',
      'quick-loan-types-msg': 'What loan types do you offer?',
      'quick-eligibility-msg': 'How can I improve my loan eligibility?',
      'quick-documents-msg': 'What documents do I need for loan application?',
      'chat-placeholder': 'Ask me about loans, eligibility, documents...',
      'send-btn': 'Send',
      'back-to-assessment': 'Back to Assessment'
    },
    'hi': {
      'loan-eligible-title': 'बधाई हो! आप पात्र हैं',
      'loan-assessment-title': 'लोन मूल्यांकन परिणाम',
      'ai-assessment': 'AI मूल्यांकन',
      'recommended-schemes': 'सुझाई गई लोन योजनाएं',
      'improvement-suggestions': 'सुधार सुझाव',
      'ask-loan-agent': 'लोनएजेंट से पूछें',
      'none-scheme': 'इनमें से कोई नहीं',
      'understand': 'मैं समझता हूं',
      'chat-with-agent': 'लोनएजेंट से चैट करें',
      'agent-welcome': 'नमस्ते! मैं आपका AI लोनएजेंट हूं। मैं लोन की जानकारी, पात्रता के प्रश्न, और आपके आवेदन को बेहतर बनाने के लिए मार्गदर्शन में आपकी सहायता कर सकता हूं। मैं आपकी कैसे सहायता कर सकता हूं?',
      'quick-loan-types': 'लोन प्रकार',
      'quick-eligibility': 'पात्रता सहायता',
      'quick-documents': 'दस्तावेज',
      'quick-loan-types-msg': 'आप कौन से लोन प्रकार ऑफर करते हैं?',
      'quick-eligibility-msg': 'मैं अपनी लोन पात्रता कैसे सुधार सकता हूं?',
      'quick-documents-msg': 'लोन आवेदन के लिए मुझे कौन से दस्तावेजों की आवश्यकता है?',
      'chat-placeholder': 'लोन, पात्रता, दस्तावेजों के बारे में पूछें...',
      'send-btn': 'भेजें',
      'back-to-assessment': 'मूल्यांकन पर वापस'
    },
    'ta': {
      'loan-eligible-title': 'வாழ்த்துக்கள்! நீங்கள் தகுதியானவர்',
      'loan-assessment-title': 'கடன் மதிப்பீட்டு முடிவுகள்',
      'ai-assessment': 'AI மதிப்பீடு',
      'recommended-schemes': 'பரிந்துரைக்கப்பட்ட கடன் திட்டங்கள்',
      'improvement-suggestions': 'மேம்பாட்டு பரிந்துரைகள்',
      'ask-loan-agent': 'லோன்ஏஜென்ட்டிடம் கேளுங்கள்',
      'none-scheme': 'இவற்றில் எதுவுமில்லை',
      'understand': 'நான் புரிந்துகொள்கிறேன்',
      'chat-with-agent': 'லோன்ஏஜென்ட்டுடன் அரட்டை',
      'agent-welcome': 'வணக்கம்! நான் உங்கள் AI லோன்ஏஜென்ட். கடன் தகவல், தகுதி கேள்விகள், மற்றும் உங்கள் விண்ணப்பத்தை மேம்படுத்த வழிகாட்டுதலில் உதவ முடியும். நான் உங்களுக்கு எப்படி உதவ முடியும்?',
      'quick-loan-types': 'கடன் வகைகள்',
      'quick-eligibility': 'தகுதி உதவி',
      'quick-documents': 'ஆவணங்கள்',
      'quick-loan-types-msg': 'நீங்கள் என்ன கடன் வகைகளை வழங்குகிறீர்கள்?',
      'quick-eligibility-msg': 'என் கடன் தகுதியை எப்படி மேம்படுத்துவது?',
      'quick-documents-msg': 'கடன் விண்ணப்பத்திற்கு எனக்கு என்ன ஆவணங்கள் தேவை?',
      'chat-placeholder': 'கடன், தகுதி, ஆவணங்களைப் பற்றி கேளுங்கள்...',
      'send-btn': 'அனுப்பு',
      'back-to-assessment': 'மதிப்பீட்டுக்கு திரும்பு'
    },
    'te': {
      'loan-eligible-title': 'అభినందనలు! మీరు అర్హులు',
      'loan-assessment-title': 'రుణ మూల్యాంకన ఫలితాలు',
      'ai-assessment': 'AI మూల్యాంకనం',
      'recommended-schemes': 'సిఫార్సు చేయబడిన రుణ పథకాలు',
      'improvement-suggestions': 'మెరుగుదల సూచనలు',
      'ask-loan-agent': 'లోన్ఏజెంట్‌ను అడగండి',
      'none-scheme': 'వీటిలో ఏదీ లేదు',
      'understand': 'నేను అర్థం చేసుకున్నాను',
      'chat-with-agent': 'లోన్ఏజెంట్‌తో చాట్',
      'agent-welcome': 'నమస్కారం! నేను మీ AI లోన్ఏజెంట్. రుణ సమాచారం, అర్హత ప్రశ్నలు, మరియు మీ దరఖాస్తును మెరుగుపరచడానికి మార్గదర్శనంలో సహాయం చేయగలను. నేను మీకు ఎలా సహాయం చేయగలను?',
      'quick-loan-types': 'రుణ రకాలు',
      'quick-eligibility': 'అర్హత సహాయం',
      'quick-documents': 'పత్రాలు',
      'quick-loan-types-msg': 'మీరు ఏ రుణ రకాలను అందిస్తారు?',
      'quick-eligibility-msg': 'నా రుణ అర్హతను ఎలా మెరుగుపరచాలి?',
      'quick-documents-msg': 'రుణ దరఖాస్తు కోసం నాకు ఏ పత్రాలు అవసరం?',
      'chat-placeholder': 'రుణాలు, అర్హత, పత్రాల గురించి అడగండి...',
      'send-btn': 'పంపండి',
      'back-to-assessment': 'మూల్యాంకనకు తిరిగి'
    }
  };
  
  return translations[language]?.[key] || translations['en'][key] || key;
}

// Save application draft to localStorage
function saveApplicationDraft(applicationId, formData, status, requiredDocs) {
  const draft = {
    applicationId: applicationId,
    formData: formData,
    status: status,
    requiredDocuments: requiredDocs,
    savedAt: new Date().toISOString(),
    userEmail: currentUser.email,
  };

  let drafts = JSON.parse(localStorage.getItem("applicationDrafts") || "[]");
  drafts.push(draft);
  localStorage.setItem("applicationDrafts", JSON.stringify(drafts));
}

// Show document upload section for approved applications
function showDocumentUploadSection(applicationId, requiredDocs) {
  // Create document type mapping
  const docTypeMapping = {
    "Identity Proof": ["Aadhaar Card", "PAN Card", "Passport Size Photos"],
    "Income Proof": [
      "Bank Statements (6 months)",
      "Salary Slips (3 months)",
      "Form 16",
      "ITR (2 years)",
    ],
    "Address Proof": [
      "Aadhaar Card",
      "Bank Statements (6 months)",
      "Property Documents",
    ],
    "PAN Card": ["PAN Card"],
    "Aadhaar Card": ["Aadhaar Card"],
    Salary: ["Salary Slips (3 months)", "Employment Certificate", "Form 16"],
    "Employment Certificate": ["Employment Certificate"],
    "Bank Statements": ["Bank Statements (6 months)"],
    "Form 16": ["Form 16"],
    "Business Registration": ["Business Registration"],
    ITR: ["ITR (2 years)"],
    "Property Documents": ["Property Documents"],
  };

  // Generate options based on required documents
  let docOptions = '<option value="">Select Document Type</option>';
  const requiredDocsList = requiredDocs.split(", ").map((doc) => doc.trim());
  const allAllowedDocs = new Set();

  requiredDocsList.forEach((requiredDoc) => {
    if (docTypeMapping[requiredDoc]) {
      docTypeMapping[requiredDoc].forEach((docType) => {
        allAllowedDocs.add(docType);
      });
    } else {
      // If exact match not found, try partial matching
      Object.keys(docTypeMapping).forEach((key) => {
        if (
          requiredDoc.toLowerCase().includes(key.toLowerCase()) ||
          key.toLowerCase().includes(requiredDoc.toLowerCase())
        ) {
          docTypeMapping[key].forEach((docType) => {
            allAllowedDocs.add(docType);
          });
        }
      });
    }
  });

  // Convert set to sorted array and create options
  Array.from(allAllowedDocs)
    .sort()
    .forEach((docType) => {
      docOptions += `<option value="${docType}">${docType}</option>`;
    });

  // Add "Other" option at the end
  docOptions += '<option value="Other">Other</option>';

  const uploadSection = document.createElement("div");
  uploadSection.id = "documentUploadSection";
  uploadSection.innerHTML = `
                <div class="form-section" style="background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 12px; margin-top: 2rem;">
                    <h3 class="section-title" style="color: #0c4a6e;">📄 Document Upload - Application ${applicationId}</h3>
                    
                    <div class="alert alert-info" style="display: block; margin-bottom: 1rem;">
                        <strong>Required Documents:</strong><br>
                        ${requiredDocs
                          .split(", ")
                          .map((doc) => `• ${doc}`)
                          .join("<br>")}
                    </div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="documentType">Document Type</label>
                            <select id="documentType" required>
                                ${docOptions}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="documentFile">Upload Document</label>
                            <input type="file" id="documentFile" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" required>
                            <small style="color: #6c757d; font-size: 0.9rem;">
                                Supported formats: PDF, JPG, PNG, DOC, DOCX (Max 5MB)
                            </small>
                        </div>
                    </div>
                    
                    <button type="button" onclick="uploadDocument('${applicationId}')" class="btn-primary" id="uploadDocBtn">
                        📎 Upload Document
                    </button>
                    
                    <div class="alert alert-success" id="uploadSuccess" style="display: none; margin-top: 1rem;"></div>
                    <div class="alert alert-error" id="uploadError" style="display: none; margin-top: 1rem;"></div>
                </div>
            `;

  // Insert after the loan application form
  const loanSection = document.getElementById("loanApplicationSection");
  loanSection.appendChild(uploadSection);
}

// Upload document function
async function uploadDocument(applicationId) {
  const documentType = document.getElementById("documentType").value;
  const documentFile = document.getElementById("documentFile").files[0];

  if (!documentType || !documentFile) {
    document.getElementById("uploadError").textContent =
      "Please select document type and file";
    document.getElementById("uploadError").style.display = "block";
    return;
  }

  // Check file size (5MB limit)
  if (documentFile.size > 5 * 1024 * 1024) {
    document.getElementById("uploadError").textContent =
      "File size must be less than 5MB";
    document.getElementById("uploadError").style.display = "block";
    return;
  }

  const uploadBtn = document.getElementById("uploadDocBtn");
  uploadBtn.disabled = true;
  uploadBtn.textContent = "📤 Uploading...";

  const formData = new FormData();
  formData.append("application_id", applicationId);
  formData.append("document_type", documentType);
  formData.append("document", documentFile);

  try {
    const response = await fetch("/upload-documents", {
      method: "POST",
      credentials: "include", // Include cookies for session management
      body: formData,
    });

    const data = await response.json();

    if (data.success) {
      document.getElementById(
        "uploadSuccess"
      ).textContent = `✅ ${documentType} uploaded successfully! Admin has been notified.`;
      document.getElementById("uploadSuccess").style.display = "block";
      document.getElementById("uploadError").style.display = "none";

      // Reset upload form
      document.getElementById("documentType").value = "";
      document.getElementById("documentFile").value = "";

      // Send email notification to admin
      notifyAdminOfDocumentUpload(
        applicationId,
        documentType,
        currentUser.email
      );
    } else {
      document.getElementById("uploadError").textContent =
        data.error || "Upload failed";
      document.getElementById("uploadError").style.display = "block";
    }
  } catch (error) {
    document.getElementById("uploadError").textContent =
      "Network error during upload";
    document.getElementById("uploadError").style.display = "block";
    console.error("Upload error:", error);
  }

  uploadBtn.disabled = false;
  uploadBtn.textContent = "📎 Upload Document";
}

// Notify admin of document upload
async function notifyAdminOfDocumentUpload(
  applicationId,
  documentType,
  userEmail
) {
  try {
    await fetch("/notify-admin-document-upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include", // Include cookies for session management
      body: JSON.stringify({
        application_id: applicationId,
        document_type: documentType,
        user_email: userEmail,
      }),
    });
  } catch (error) {
    console.error("Admin notification error:", error);
  }
}

// New drafts functionality for objected applications
function loadDraftsFromServer() {
  const draftsContainer = document.getElementById("draftsContainer");
  
  // Show loading state
  draftsContainer.innerHTML = `
    <div style="text-align: center; padding: 2rem;">
      <div style="font-size: 2rem; margin-bottom: 1rem;">⏳</div>
      <p>Loading your draft applications...</p>
    </div>
  `;

  // Get drafts from server
  fetch("/user-drafts", {
    credentials: "include",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success && data.drafts.length > 0) {
        let draftsHTML = "";
        data.drafts.forEach((draft) => {
          const formattedDate = new Date(draft.objection_created_at).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          });

          draftsHTML += `
            <div class="application-card objection-card">
              <div class="application-header">
                <div class="application-id">📋 ${draft.application_id}</div>
                <div class="status-badge objection">OBJECTION RAISED</div>
              </div>
              
              <div class="application-details">
                <div class="detail-item">
                  <div class="detail-label">Loan Type</div>
                  <div class="detail-value">${draft.loan_type}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-label">Loan Amount</div>
                  <div class="detail-value">₹${parseInt(draft.loan_amount).toLocaleString()}</div>
                </div>
                <div class="detail-item">
                  <div class="detail-label">Objection Date</div>
                  <div class="detail-value">${formattedDate}</div>
                </div>
              </div>
              
              <div class="objection-details">
                <div class="objection-reason">
                  <h4>🚫 Objection Reason:</h4>
                  <p>${draft.objection_reason}</p>
                </div>
                <div class="requested-documents">
                  <h4>📄 Requested Documents:</h4>
                  <p>${draft.requested_documents}</p>
                </div>
                ${draft.current_documents ? `
                  <div class="current-documents">
                    <h4>📎 Current Documents:</h4>
                    <p>${draft.current_documents}</p>
                  </div>
                ` : ''}
              </div>
              
              <div class="application-actions">
                <button onclick="uploadDocumentsForDraft('${draft.application_id}', '${draft.requested_documents}')" class="btn-small btn-upload">
                  📎 Upload New Documents
                </button>
                <button onclick="resubmitApplication('${draft.application_id}')" class="btn-small btn-resubmit">
                  🔄 Resubmit Application
                </button>
                <button onclick="viewDraftDetails('${draft.application_id}')" class="btn-small btn-view">
                  👁️ View Full Details
                </button>
              </div>
            </div>
          `;
        });

        draftsContainer.innerHTML = draftsHTML;
      } else {
        draftsContainer.innerHTML = `
          <div class="empty-state">
            <div style="text-align: center; padding: 3rem; color: #6c757d;">
              <div style="font-size: 4rem; margin-bottom: 1rem;">💾</div>
              <h4>No Drafts Found</h4>
              <p>Applications with objections will appear here for resubmission.</p>
              <button onclick="switchAppTab('newApplication')" class="btn-primary" style="margin-top: 1rem; width: auto; padding: 0.8rem 2rem;">
                Create New Application
              </button>
            </div>
          </div>
        `;
      }
    })
    .catch((error) => {
      console.error("Error loading drafts:", error);
      draftsContainer.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #dc3545;">
          <div style="font-size: 4rem; margin-bottom: 1rem;">❌</div>
          <h4>Error Loading Drafts</h4>
          <p>Please try again later.</p>
          <button onclick="loadDraftsFromServer()" class="btn-primary" style="margin-top: 1rem; width: auto; padding: 0.8rem 2rem;">
            Retry
          </button>
        </div>
      `;
    });
}

function resubmitApplication(applicationId) {
  if (!confirm('Are you sure you want to resubmit this application? It will be sent for review again.')) {
    return;
  }

  // Show loading
  const button = event.target;
  const originalText = button.innerHTML;
  button.innerHTML = '⏳ Resubmitting...';
  button.disabled = true;

  fetch('/resubmit-application', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      application_id: applicationId
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('✅ Application resubmitted successfully! You will receive an email confirmation.');
      // Refresh the drafts view
      loadDraftsFromServer();
      // Also refresh history
      loadHistory();
    } else {
      alert('❌ Error: ' + (data.error || 'Failed to resubmit application'));
      button.innerHTML = originalText;
      button.disabled = false;
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('❌ Network error. Please try again.');
    button.innerHTML = originalText;
    button.disabled = false;
  });
}

function viewDraftDetails(applicationId) {
  // This function can be expanded to show full application details
  alert(`Viewing details for application ${applicationId}. This feature can be expanded to show full application information.`);
}
