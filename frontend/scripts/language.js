// Language translation system
const translations = {
  en: {
    // Common elements
    'app-title': '🤖 LoanAgent',
    'app-subtitle': 'Your AI-Powered Banking Assistant',
    'nav-apply': '💼 Apply for Loan',
    'nav-staff': '👩‍💼 Staff Login',
    'nav-agent': '🤖 Loan Agent',
    
    // Main page - Chat interface
    'chat-title': '💬 Chat with LoanAgent',
    'chat-status': 'Online • Ready to help with your banking needs',
    'welcome-message': `Hello! I'm LoanAgent, your AI banking assistant. I can help you with:
<br><br>
• Loan information and eligibility
<br>• Account inquiries  
<br>• Banking services
<br>• Application status
<br><br>
How can I assist you today?`,
    'quick-loan-types': 'Loan Types',
    'quick-eligibility': 'Eligibility Check',
    'quick-documents': 'Required Documents',
    'quick-approval': 'Approval Time',
    'chat-placeholder': 'Type your message here...',
    'send-btn': 'Send',
    
    // Loan application page
    'loan-app-title': '💼 Loan Application',
    'loan-app-subtitle': 'Apply for Personal, Home, or Business Loans',
    'personal-info': 'Personal Information',
    'full-name': 'Full Name',
    'full-name-placeholder': 'Enter your full name',
    'email-address': 'Email Address',
    'email-placeholder': 'Enter your email address',
    'phone-number': 'Phone Number',
    'phone-placeholder': 'Enter your phone number',
    'address': 'Address',
    'address-placeholder': 'Enter your complete address',
    'loan-details': 'Loan Details',
    'loan-type': 'Loan Type',
    'select-loan-type': 'Select loan type',
    'personal-loan': 'Personal Loan',
    'home-loan': 'Home Loan',
    'business-loan': 'Business Loan',
    'loan-amount': 'Loan Amount (₹)',
    'loan-amount-placeholder': 'Enter desired loan amount',
    'loan-purpose': 'Loan Purpose',
    'loan-purpose-placeholder': 'Describe the purpose of the loan',
    'employment-info': 'Employment Information',
    'employment-type': 'Employment Type',
    'select-employment': 'Select employment type',
    'salaried': 'Salaried',
    'self-employed': 'Self-Employed',
    'business-owner': 'Business Owner',
    'monthly-income': 'Monthly Income (₹)',
    'monthly-income-placeholder': 'Enter your monthly income',
    'company-name': 'Company/Organization Name',
    'company-placeholder': 'Enter company or organization name',
    'documents': 'Documents',
    'upload-documents': 'Upload Required Documents',
    'aadhaar-card': 'Aadhaar Card',
    'choose-file': 'Choose file',
    'submit-application': 'Submit Application',
    'drafts-section': 'Your Drafts',
    'objected-applications': 'Applications with Objections',
    'no-drafts': 'No draft applications found.',
    'application-id': 'Application ID',
    'objection-reason': 'Objection Reason',
    'actions': 'Actions',
    'resubmit': 'Resubmit',
    
    // Staff portal
    'staff-title': '👩‍💼 Staff Portal',
    'staff-subtitle': 'Secure Staff Access to Banking Administration',
    'staff-login': 'Staff Login',
    'username': 'Username',
    'username-placeholder': 'Enter your username',
    'password': 'Password',
    'password-placeholder': 'Enter your password',
    'login-btn': 'Login',
    'admin-dashboard': 'Admin Dashboard',
    'loan-applications': 'Loan Applications',
    'pending-review': 'Pending Review',
    'approve': 'Approve',
    'reject': 'Reject',
    'view-details': 'View Details',
    'application-details': 'Application Details',
    'applicant-info': 'Applicant Information',
    'loan-info': 'Loan Information',
    'employment-details': 'Employment Details',
    'uploaded-documents': 'Uploaded Documents',
    'status': 'Status',
    'pending': 'Pending',
    'approved': 'Approved',
    'rejected': 'Rejected',
    'review-application': 'Review Application',
    'objection-reason-label': 'Objection Reason',
    'objection-placeholder': 'Enter reason for objection...',
    'submit-objection': 'Submit with Objection',
    
    // Additional form fields
    'date-of-birth': 'Date of Birth',
    'gender': 'Gender',
    'select-gender': 'Select Gender',
    'male': 'Male',
    'female': 'Female',
    'prefer-not-say': 'Prefer not to say',
    'marital-status': 'Marital Status',
    'select-status': 'Select Status',
    'single': 'Single',
    'married': 'Married',
    'divorced': 'Divorced',
    'widowed': 'Widowed',
    'nationality': 'Nationality',
    'nationality-placeholder': 'Indian',
    'contact-number': 'Contact Number',
    'contact-placeholder': '+91 9876543210',
    'freelancer': 'Freelancer',
    'experience': 'Work Experience (Years)',
    'experience-placeholder': 'Enter years of experience',
    'annual-income': 'Annual Income (₹)',
    'annual-income-placeholder': 'Enter your annual income',
    'employer-name': 'Employer Name',
    'employer-placeholder': 'Company/Organization name',
    'loan-amount-needed': 'Loan Amount Needed (₹)',
    'loan-purpose-detailed': 'Purpose of Loan',
    'loan-tenure': 'Loan Tenure (Months)',
    'tenure-placeholder': 'Enter loan tenure in months',
    'existing-loans': 'Any Existing Loans?',
    'yes': 'Yes',
    'no': 'No',
    'submit-btn': 'Submit Application',
    'clear-session': 'Clear Session',
    'new-loan-app': 'New Loan Application',
    'personal-details': 'Personal Details',
    'employment-income': 'Employment & Income Details',
    'loan-specific': 'Loan Specific Details',
    'app-drafts': 'Application Drafts',
    'app-history': 'Application History',
    
        // Staff portal additional
    'access-admin': 'प्रशासनिक डैशबोर्ड तक पहुंच',
    'staff-username-placeholder': 'अपना स्टाफ उपयोगकर्ता नाम दर्ज करें',
    'staff-password-placeholder': 'अपना पासवर्ड दर्ज करें',
    
    // Admin dashboard
    'admin-dashboard': '🏦 बैंकिंग एडमिन डैशबोर्ड',
    'logout': 'लॉगआउट',
    'analytics': '📊 विश्लेषण',
    'loan-applications': '📋 लोन आवेदन',
    'pending-applications': 'लंबित आवेदन',
    'approved-applications': 'अनुमोदित आवेदन',
    'rejected-applications': 'अस्वीकृत आवेदन',
    'name': 'नाम',
    'email': 'ईमेल',
    'amount': 'राशि',
        'date': 'Date',
    'welcome': 'Welcome',
    
    // Loan Assessment Popup
    'loan-eligible-title': 'Congratulations! You are Eligible',
    'loan-assessment-title': 'Loan Assessment Results',
    'ai-assessment': 'AI Assessment',
    'recommended-schemes': 'Recommended Loan Schemes',
    'improvement-suggestions': 'Improvement Suggestions',
    'ask-loan-agent': 'Ask LoanAgent',
    'none-scheme': 'None of These',
    'understand': 'I Understand',
    'scheme-details': 'View Details',
    'select-scheme': 'Select This Scheme',
    'continue-scheme': 'Continue with this Scheme',
    'back-options': 'Back to Options',
    'document-upload-title': 'Document Upload Required',
    'upload-documents': 'Upload Documents',
    'complete-application': 'Complete Application',
    'upload-later': 'Upload Later'
  },
  
  hi: {
  },
  
  hi: {
    // Common elements
    'app-title': '🤖 लोनएजेंट',
    'app-subtitle': 'आपका AI-संचालित बैंकिंग सहायक',
    'nav-apply': '💼 लोन के लिए आवेदन करें',
    'nav-staff': '👩‍💼 स्टाफ लॉगिन',
    'nav-agent': '🤖 लोन एजेंट',
    
    // Main page - Chat interface
    'chat-title': '💬 लोनएजेंट से चैट करें',
    'chat-status': 'ऑनलाइन • आपकी बैंकिंग आवश्यकताओं में मदद के लिए तैयार',
    'welcome-message': `नमस्ते! मैं लोनएजेंट हूं, आपका AI बैंकिंग सहायक। मैं आपकी मदद कर सकता हूं:
<br><br>
• लोन की जानकारी और पात्रता
<br>• खाता पूछताछ  
<br>• बैंकिंग सेवाएं
<br>• आवेदन की स्थिति
<br><br>
आज मैं आपकी कैसे सहायता कर सकता हूं?`,
    'quick-loan-types': 'लोन प्रकार',
    'quick-eligibility': 'पात्रता जांच',
    'quick-documents': 'आवश्यक दस्तावेज',
    'quick-approval': 'अनुमोदन समय',
    'chat-placeholder': 'यहाँ अपना संदेश टाइप करें...',
    'send-btn': 'भेजें',
    
    // Loan application page
    'loan-app-title': '💼 लोन आवेदन',
    'loan-app-subtitle': 'व्यक्तिगत, गृह या व्यावसायिक लोन के लिए आवेदन करें',
    'personal-info': 'व्यक्तिगत जानकारी',
    'full-name': 'पूरा नाम',
    'full-name-placeholder': 'अपना पूरा नाम दर्ज करें',
    'email-address': 'ईमेल पता',
    'email-placeholder': 'अपना ईमेल पता दर्ज करें',
    'phone-number': 'फोन नंबर',
    'phone-placeholder': 'अपना फोन नंबर दर्ज करें',
    'address': 'पता',
    'address-placeholder': 'अपना पूरा पता दर्ज करें',
    'loan-details': 'लोन विवरण',
    'loan-type': 'लोन प्रकार',
    'select-loan-type': 'लोन प्रकार चुनें',
    'personal-loan': 'व्यक्तिगत लोन',
    'home-loan': 'गृह लोन',
    'business-loan': 'व्यावसायिक लोन',
    'loan-amount': 'लोन राशि (₹)',
    'loan-amount-placeholder': 'वांछित लोन राशि दर्ज करें',
    'loan-purpose': 'लोन का उद्देश्य',
    'loan-purpose-placeholder': 'लोन के उद्देश्य का वर्णन करें',
    'employment-info': 'रोजगार की जानकारी',
    'employment-type': 'रोजगार प्रकार',
    'select-employment': 'रोजगार प्रकार चुनें',
    'salaried': 'वेतनभोगी',
    'self-employed': 'स्व-रोजगार',
    'business-owner': 'व्यापार मालिक',
    'monthly-income': 'मासिक आय (₹)',
    'monthly-income-placeholder': 'अपनी मासिक आय दर्ज करें',
    'company-name': 'कंपनी/संगठन का नाम',
    'company-placeholder': 'कंपनी या संगठन का नाम दर्ज करें',
    'documents': 'दस्तावेज',
    'upload-documents': 'आवश्यक दस्तावेज अपलोड करें',
    'aadhaar-card': 'आधार कार्ड',
    'choose-file': 'फाइल चुनें',
    'submit-application': 'आवेदन जमा करें',
    'drafts-section': 'आपके ड्राफ्ट',
    'objected-applications': 'आपत्ति वाले आवेदन',
    'no-drafts': 'कोई ड्राफ्ट आवेदन नहीं मिला।',
    'application-id': 'आवेदन आईडी',
    'objection-reason': 'आपत्ति का कारण',
    'actions': 'कार्य',
    'resubmit': 'पुनः जमा करें',
    
    // Staff portal
    'staff-title': '👩‍💼 स्टाफ पोर्टल',
    'staff-subtitle': 'बैंकिंग प्रशासन के लिए सुरक्षित स्टाफ पहुंच',
    'staff-login': 'स्टाफ लॉगिन',
    'username': 'उपयोगकर्ता नाम',
    'username-placeholder': 'अपना उपयोगकर्ता नाम दर्ज करें',
    'password': 'पासवर्ड',
    'password-placeholder': 'अपना पासवर्ड दर्ज करें',
    'login-btn': 'लॉगिन',
    'admin-dashboard': 'एडमिन डैशबोर्ड',
    'loan-applications': 'लोन आवेदन',
    'pending-review': 'समीक्षा के लिए लंबित',
    'approve': 'अनुमोदित करें',
    'reject': 'अस्वीकार करें',
    'view-details': 'विवरण देखें',
    'application-details': 'आवेदन विवरण',
    'applicant-info': 'आवेदक की जानकारी',
    'loan-info': 'लोन की जानकारी',
    'employment-details': 'रोजगार विवरण',
    'uploaded-documents': 'अपलोड किए गए दस्तावेज',
    'status': 'स्थिति',
    'pending': 'लंबित',
    'approved': 'अनुमोदित',
    'rejected': 'अस्वीकृत',
    'review-application': 'आवेदन की समीक्षा करें',
    'objection-reason-label': 'आपत्ति का कारण',
    'objection-placeholder': 'आपत्ति का कारण दर्ज करें...',
    'submit-objection': 'आपत्ति के साथ जमा करें',
    
    // Additional form fields
    'date-of-birth': 'जन्म तिथि',
    'gender': 'लिंग',
    'select-gender': 'लिंग चुनें',
    'male': 'पुरुष',
    'female': 'महिला',
    'prefer-not-say': 'नहीं कहना चाहते',
    'marital-status': 'वैवाहिक स्थिति',
    'select-status': 'स्थिति चुनें',
    'single': 'अविवाहित',
    'married': 'विवाहित',
    'divorced': 'तलाकशुदा',
    'widowed': 'विधवा',
    'nationality': 'राष्ट्रीयता',
    'nationality-placeholder': 'भारतीय',
    'contact-number': 'संपर्क नंबर',
    'contact-placeholder': '+91 9876543210',
    'freelancer': 'फ्रीलांसर',
    'experience': 'कार्य अनुभव (वर्ष)',
    'experience-placeholder': 'अनुभव के वर्ष दर्ज करें',
    'annual-income': 'वार्षिक आय (₹)',
    'annual-income-placeholder': 'अपनी वार्षिक आय दर्ज करें',
    'employer-name': 'नियोक्ता का नाम',
    'employer-placeholder': 'कंपनी/संगठन का नाम',
    'loan-amount-needed': 'आवश्यक लोन राशि (₹)',
    'loan-purpose-detailed': 'लोन का उद्देश्य',
    'loan-tenure': 'लोन अवधि (महीने)',
    'tenure-placeholder': 'महीनों में लोन अवधि दर्ज करें',
    'existing-loans': 'कोई मौजूदा लोन?',
    'yes': 'हाँ',
    'no': 'नहीं',
    'submit-btn': 'आवेदन जमा करें',
    'clear-session': 'सेशन साफ करें',
    'new-loan-app': 'नया लोन आवेदन',
    'personal-details': 'व्यक्तिगत विवरण',
    'employment-income': 'रोजगार और आय विवरण',
    'loan-specific': 'लोन विशिष्ट विवरण',
    'app-drafts': 'आवेदन ड्राफ्ट',
    'app-history': 'आवेदन इतिहास',
    
    // Loan Assessment Popup
    'loan-eligible-title': 'बधाई हो! आप पात्र हैं',
    'loan-assessment-title': 'लोन मूल्यांकन परिणाम',
    'ai-assessment': 'AI मूल्यांकन',
    'recommended-schemes': 'सुझाई गई लोन योजनाएं',
    'improvement-suggestions': 'सुधार सुझाव',
    'ask-loan-agent': 'लोनएजेंट से पूछें',
    'none-scheme': 'इनमें से कोई नहीं',
    'understand': 'मैं समझता हूं',
    'scheme-details': 'विवरण देखें',
    'select-scheme': 'यह योजना चुनें',
    'continue-scheme': 'इस योजना के साथ जारी रखें',
    'back-options': 'विकल्पों पर वापस',
    'document-upload-title': 'दस्तावेज अपलोड आवश्यक',
    'upload-documents': 'दस्तावेज अपलोड करें',
    'complete-application': 'आवेदन पूरा करें',
    'upload-later': 'बाद में अपलोड करें'
  },
  
  ta: {
    // Common elements
    'app-title': '🤖 லோன்ஏஜென்ட்',
    'app-subtitle': 'உங்கள் AI-இயக்கப்படும் வங்கி உதவியாளர்',
    'nav-apply': '💼 கடனுக்கு விண்ணப்பிக்கவும்',
    'nav-staff': '👩‍💼 ஊழியர் உள்நுழைவு',
    'nav-agent': '🤖 கடன் ஏஜென்ட்',
    
    // Main page - Chat interface
    'chat-title': '💬 லோன்ஏஜென்ட்டுடன் அரட்டையடிக்கவும்',
    'chat-status': 'ஆன்லைன் • உங்கள் வங்கித் தேவைகளுக்கு உதவ தயார்',
    'welcome-message': `வணக்கம்! நான் லோன்ஏஜென்ட், உங்கள் AI வங்கி உதவியாளர். நான் உங்களுக்கு உதவ முடியும்:
<br><br>
• கடன் தகவல் மற்றும் தகுதி
<br>• கணக்கு விசாரணைகள்  
<br>• வங்கி சேவைகள்
<br>• விண்ணப்ப நிலை
<br><br>
இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?`,
    'quick-loan-types': 'கடன் வகைகள்',
    'quick-eligibility': 'தகுதி சரிபார்ப்பு',
    'quick-documents': 'தேவையான ஆவணங்கள்',
    'quick-approval': 'அனுமதி நேரம்',
    'chat-placeholder': 'உங்கள் செய்தியை இங்கே தட்டச்சு செய்யவும்...',
    'send-btn': 'அனுப்பு',
    
    // Loan application page
    'loan-app-title': '💼 கடன் விண்ணப்பம்',
    'loan-app-subtitle': 'தனிப்பட்ட, வீடு அல்லது வணிக கடன்களுக்கு விண்ணப்பிக்கவும்',
    'personal-info': 'தனிப்பட்ட தகவல்',
    'full-name': 'முழு பெயர்',
    'full-name-placeholder': 'உங்கள் முழு பெயரை உள்ளிடவும்',
    'email-address': 'மின்னஞ்சல் முகவரி',
    'email-placeholder': 'உங்கள் மின்னஞ்சல் முகவரியை உள்ளிடவும்',
    'phone-number': 'தொலைபேசி எண்',
    'phone-placeholder': 'உங்கள் தொலைபேசி எண்ணை உள்ளிடவும்',
    'address': 'முகவரி',
    'address-placeholder': 'உங்கள் முழு முகவரியை உள்ளிடவும்',
    'loan-details': 'கடன் விவரங்கள்',
    'loan-type': 'கடன் வகை',
    'select-loan-type': 'கடன் வகையைத் தேர்ந்தெடுக்கவும்',
    'personal-loan': 'தனிப்பட்ட கடன்',
    'home-loan': 'வீட்டுக் கடன்',
    'business-loan': 'வணிகக் கடன்',
    'loan-amount': 'கடன் தொகை (₹)',
    'loan-amount-placeholder': 'விரும்பிய கடன் தொகையை உள்ளிடவும்',
    'loan-purpose': 'கடனின் நோக்கம்',
    'loan-purpose-placeholder': 'கடனின் நோக்கத்தை விவரிக்கவும்',
    'employment-info': 'வேலைவாய்ப்பு தகவல்',
    'employment-type': 'வேலைவாய்ப்பு வகை',
    'select-employment': 'வேலைவாய்ப்பு வகையைத் தேர்ந்தெடுக்கவும்',
    'salaried': 'சம்பளம் பெறுபவர்',
    'self-employed': 'சுயதொழில்',
    'business-owner': 'வணிக உரிமையாளர்',
    'monthly-income': 'மாதாந்திர வருமானம் (₹)',
    'monthly-income-placeholder': 'உங்கள் மாதாந்திர வருமானத்தை உள்ளிடவும்',
    'company-name': 'நிறுவனம்/அமைப்பு பெயர்',
    'company-placeholder': 'நிறுவனம் அல்லது அமைப்பின் பெயரை உள்ளிடவும்',
    'documents': 'ஆவணங்கள்',
    'upload-documents': 'தேவையான ஆவணங்களை பதிவேற்றவும்',
    'aadhaar-card': 'ஆதார் அட்டை',
    'choose-file': 'கோப்பைத் தேர்ந்தெடுக்கவும்',
    'submit-application': 'விண்ணப்பத்தைச் சமர்ப்பிக்கவும்',
    'drafts-section': 'உங்கள் வரைவுகள்',
    'objected-applications': 'எதிர்ப்புகள் உள்ள விண்ணப்பங்கள்',
    'no-drafts': 'வரைவு விண்ணப்பங்கள் எதுவும் இல்லை.',
    'application-id': 'விண்ணப்ப ID',
    'objection-reason': 'எதிர்ப்பின் காரணம்',
    'actions': 'செயல்கள்',
    'resubmit': 'மீண்டும் சமர்ப்பிக்கவும்',
    
    // Staff portal
    'staff-title': '👩‍💼 ஊழியர் போர்ட்டல்',
    'staff-subtitle': 'வங்கி நிர்வாகத்திற்கான பாதுகாப்பான ஊழியர் அணுகல்',
    'staff-login': 'ஊழியர் உள்நுழைவு',
    'username': 'பயனர் பெயர்',
    'username-placeholder': 'உங்கள் பயனர் பெயரை உள்ளிடவும்',
    'password': 'கடவுச்சொல்',
    'password-placeholder': 'உங்கள் கடவுச்சொல்லை உள்ளிடவும்',
    'login-btn': 'உள்நுழை',
    'admin-dashboard': 'நிர்வாக டாஷ்போர்டு',
    'loan-applications': 'கடன் விண்ணப்பங்கள்',
    'pending-review': 'மதிப்பாய்வு நிலுவையில்',
    'approve': 'அனுமதி',
    'reject': 'நிராகரி',
    'view-details': 'விவரங்களைப் பார்க்கவும்',
    'application-details': 'விண்ணப்ப விவரங்கள்',
    'applicant-info': 'விண்ணப்பதாரர் தகவல்',
    'loan-info': 'கடன் தகவல்',
    'employment-details': 'வேலைவாய்ப்பு விவரங்கள்',
    'uploaded-documents': 'பதிவேற்றப்பட்ட ஆவணங்கள்',
    'status': 'நிலை',
    'pending': 'நிலுவையில்',
    'approved': 'அனுமதிக்கப்பட்டது',
    'rejected': 'நிராகரிக்கப்பட்டது',
    'review-application': 'விண்ணப்பத்தை மதிப்பாய்வு செய்யவும்',
    'objection-reason-label': 'எதிர்ப்பின் காரணம்',
    'objection-placeholder': 'எதிர்ப்பின் காரணத்தை உள்ளிடவும்...',
    'submit-objection': 'எதிர்ப்புடன் சமர்ப்பிக்கவும்'
  },
  
  te: {
    // Common elements
    'app-title': '🤖 లోన్ఏజెంట్',
    'app-subtitle': 'మీ AI-శక్తిగల బ్యాంకింగ్ సహాయకుడు',
    'nav-apply': '💼 రుణం కోసం దరఖాస్తు చేయండి',
    'nav-staff': '👩‍💼 సిబ్బంది లాగిన్',
    'nav-agent': '🤖 లోన్ ఏజెంట్',
    
    // Loan application page
    'loan-app-title': '💼 రుణ దరఖాస్తు',
    'loan-app-subtitle': 'వ్యక్తిగత, ఇల్లు లేదా వ్యాపార రుణాల కోసం దరఖాస్తు చేయండి',
    
    // Staff portal
    'staff-title': '👩‍💼 సిబ్బంది పోర్టల్',
    'staff-subtitle': 'బ్యాంకింగ్ పరిపాలనకు సురక్షిత సిబ్బంది యాక్సెస్',
    
    // Chat interface
    'chat-title': '💬 లోన్ఏజెంట్తో చాట్ చేయండి',
    'chat-status': 'ఆన్‌లైన్ • మీ బ్యాంకింగ్ అవసరాలలో సహాయం చేయడానికి సిద్ధంగా ఉంది',
    'welcome-message': `నమస్కారం! నేను లోన్ఏజెంట్, మీ AI బ్యాంకింగ్ సహాయకుడు. నేను మీకు సహాయం చేయగలను:
<br><br>
• రుణ సమాచారం మరియు అర్హత
<br>• ఖాతా విచారణలు  
<br>• బ్యాంకింగ్ సేవలు
<br>• దరఖాస్తు స్థితి
<br><br>
ఈ రోజు నేను మీకు ఎలా సహాయం చేయగలను?`,
    'quick-loan-types': 'రుణ రకాలు',
    'quick-eligibility': 'అర్హత తనిఖీ',
    'quick-documents': 'అవసరమైన పత్రాలు',
    'quick-approval': 'ఆమోదం సమయం',
    'chat-placeholder': 'మీ సందేశాన్ని ఇక్కడ టైప్ చేయండి...',
    'send-btn': 'పంపండి',
    
    // Loan application page
    'loan-app-title': '💼 రుణ దరఖాస్తు',
    'loan-app-subtitle': 'వ్యక్తిగత, ఇల్లు లేదా వ్యాపార రుణాల కోసం దరఖాస్తు చేయండి',
    'personal-info': 'వ్యక్తిగత సమాచారం',
    'full-name': 'పూర్తి పేరు',
    'full-name-placeholder': 'మీ పూర్తి పేరును నమోదు చేయండి',
    'email-address': 'ఇమెయిల్ చిరునామా',
    'email-placeholder': 'మీ ఇమెయిల్ చిరునామాను నమోదు చేయండి',
    'phone-number': 'ఫోన్ నంబర్',
    'phone-placeholder': 'మీ ఫోన్ నంబర్‌ను నమోదు చేయండి',
    'address': 'చిరునామా',
    'address-placeholder': 'మీ పూర్తి చిరునామాను నమోదు చేయండి',
    'loan-details': 'రుణ వివరాలు',
    'loan-type': 'రుణ రకం',
    'select-loan-type': 'రుణ రకాన్ని ఎంచుకోండి',
    'personal-loan': 'వ్యక్తిగత రుణం',
    'home-loan': 'గృహ రుణం',
    'business-loan': 'వ్యాపార రుణం',
    'loan-amount': 'రుణ మొత్తం (₹)',
    'loan-amount-placeholder': 'కావాల్సిన రుణ మొత్తాన్ని నమోదు చేయండి',
    'loan-purpose': 'రుణ ప్రయోజనం',
    'loan-purpose-placeholder': 'రుణ ప్రయోజనాన్ని వివరించండి',
    'employment-info': 'ఉపాధి సమాచారం',
    'employment-type': 'ఉపాధి రకం',
    'select-employment': 'ఉపాధి రకాన్ని ఎంచుకోండి',
    'salaried': 'జీతం పొందేవారు',
    'self-employed': 'స్వయం ఉపాధి',
    'business-owner': 'వ్యాపార యజమాని',
    'monthly-income': 'నెలవారీ ఆదాయం (₹)',
    'monthly-income-placeholder': 'మీ నెలవారీ ఆదాయాన్ని నమోదు చేయండి',
    'company-name': 'కంపెనీ/సంస్థ పేరు',
    'company-placeholder': 'కంపెనీ లేదా సంస్థ పేరును నమోదు చేయండి',
    'documents': 'పత్రాలు',
    'upload-documents': 'అవసరమైన పత్రాలను అప్‌లోడ్ చేయండి',
    'aadhaar-card': 'ఆధార్ కార్డ్',
    'choose-file': 'ఫైల్ ఎంచుకోండి',
    'submit-application': 'దరఖాస్తును సమర్పించండి',
    'drafts-section': 'మీ డ్రాఫ్ట్‌లు',
    'objected-applications': 'అభ్యంతరాలతో దరఖాస్తులు',
    'no-drafts': 'డ్రాఫ్ట్ దరఖాస్తులు ఏవీ కనుగొనబడలేదు.',
    'application-id': 'దరఖాస్తు ID',
    'objection-reason': 'అభ్యంతర కారణం',
    'actions': 'చర్యలు',
    'resubmit': 'మళ్లీ సమర్పించండి',
    
    // Staff portal
    'staff-title': '👩‍💼 సిబ్బంది పోర్టల్',
    'staff-subtitle': 'బ్యాంకింగ్ పరిపాలనకు సురక్షిత సిబ్బంది యాక్సెస్',
    'staff-login': 'సిబ్బంది లాగిన్',
    'username': 'వినియోగదారు పేరు',
    'username-placeholder': 'మీ వినియోగదారు పేరును నమోదు చేయండి',
    'password': 'పాస్‌వర్డ్',
    'password-placeholder': 'మీ పాస్‌వర్డ్‌ను నమోదు చేయండి',
    'login-btn': 'లాగిన్',
    'admin-dashboard': 'అడ్మిన్ డ్యాష్‌బోర్డ్',
    'loan-applications': 'రుణ దరఖాస్తులు',
    'pending-review': 'సమీక్ష పెండింగ్‌లో',
    'approve': 'ఆమోదించండి',
    'reject': 'తిరస్కరించండి',
    'view-details': 'వివరాలను చూడండి',
    'application-details': 'దరఖాస్తు వివరాలు',
    'applicant-info': 'దరఖాస్తుదారు సమాచారం',
    'loan-info': 'రుణ సమాచారం',
    'employment-details': 'ఉపాధి వివరాలు',
    'uploaded-documents': 'అప్‌లోడ్ చేసిన పత్రాలు',
    'status': 'స్థితి',
    'pending': 'పెండింగ్‌లో',
    'approved': 'ఆమోదించబడింది',
    'rejected': 'తిరస్కరించబడింది',
    'review-application': 'దరఖాస్తును సమీక్షించండి',
    'objection-reason-label': 'అభ్యంతర కారణం',
    'objection-placeholder': 'అభ్యంతర కారణాన్ని నమోదు చేయండి...',
    'submit-objection': 'అభ్యంతరంతో సమర్పించండి'
  }
};

// Language data with flags
const languages = {
  en: { name: 'English', flag: '🇺🇸' },
  hi: { name: 'हिंदी', flag: '🇮🇳' },
  ta: { name: 'தமிழ்', flag: '🇮🇳' },
  te: { name: 'తెలుగు', flag: '🇮🇳' }
};

// Current language
let currentLanguage = localStorage.getItem('selectedLanguage') || 'en';

// Initialize language system
document.addEventListener('DOMContentLoaded', function() {
  setupLanguageSelector();
  applyLanguage(currentLanguage);
});

function setupLanguageSelector() {
  const languageBtn = document.getElementById('languageBtn');
  const languageMenu = document.getElementById('languageMenu');
  const languageDropdown = languageBtn?.parentElement;
  
  if (!languageBtn || !languageMenu) return;
  
  // Toggle dropdown on button click
  languageBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    languageDropdown.classList.toggle('active');
  });
  
  // Close dropdown when clicking outside
  document.addEventListener('click', function() {
    languageDropdown.classList.remove('active');
  });
  
  // Prevent dropdown from closing when clicking inside menu
  languageMenu.addEventListener('click', function(e) {
    e.stopPropagation();
  });
  
  // Update current language display
  updateLanguageDisplay();
}

function updateLanguageDisplay() {
  const currentFlag = document.getElementById('currentFlag');
  const currentLang = document.getElementById('currentLang');
  
  if (currentFlag && currentLang && languages[currentLanguage]) {
    currentFlag.textContent = languages[currentLanguage].flag;
    currentLang.textContent = languages[currentLanguage].name;
  }
}

function changeLanguage(langCode) {
  if (!translations[langCode]) return;
  
  currentLanguage = langCode;
  localStorage.setItem('selectedLanguage', langCode);
  
  // Close dropdown
  const languageDropdown = document.querySelector('.language-dropdown');
  if (languageDropdown) {
    languageDropdown.classList.remove('active');
  }
  
  // Update display and apply translations
  updateLanguageDisplay();
  applyLanguage(langCode);
  
  // Show language change notification
  showLanguageChangeNotification(languages[langCode].name);
}

function applyLanguage(langCode) {
  const langTranslations = translations[langCode];
  if (!langTranslations) return;
  
  // Translate elements with data-translate attribute
  document.querySelectorAll('[data-translate]').forEach(element => {
    const key = element.getAttribute('data-translate');
    if (langTranslations[key]) {
      element.innerHTML = langTranslations[key];
    }
  });
  
  // Translate placeholder attributes
  document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
    const key = element.getAttribute('data-translate-placeholder');
    if (langTranslations[key]) {
      element.placeholder = langTranslations[key];
    }
  });
  
  // Update document language attribute
  document.documentElement.lang = langCode;
  
  // Translate dynamic content
  translateDynamicContent();
}

function showLanguageChangeNotification(languageName) {
  // Create notification element
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    z-index: 10000;
    font-weight: 500;
    font-size: 14px;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  `;
  notification.textContent = `Language changed to ${languageName}`;
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 100);
  
  // Animate out and remove
  setTimeout(() => {
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 2000);
}

// Export functions for global use
window.changeLanguage = changeLanguage;
window.applyLanguage = applyLanguage;

// Add function to translate dynamic content and error messages
window.translateText = function(text, targetLanguage = currentLanguage) {
  const langTranslations = translations[targetLanguage];
  if (!langTranslations) return text;
  
  // Common error message translations
  const errorTranslations = {
    'en': {
      'Failed to authenticate': 'Failed to authenticate with IBM Cloud',
      'Query field cannot': 'Query field cannot be empty',
      'Invalid request format': 'Invalid request format',
      'Session cleared': 'Session cleared successfully',
      'Login successful': 'Login successful',
      'Invalid credentials': 'Invalid credentials'
    },
    'hi': {
      'Failed to authenticate': 'IBM Cloud के साथ प्रमाणीकरण में विफल',
      'Query field cannot': 'क्वेरी फ़ील्ड खाली नहीं हो सकती',
      'Invalid request format': 'अमान्य अनुरोध प्रारूप',
      'Session cleared': 'सेशन सफलतापूर्वक साफ़ किया गया',
      'Login successful': 'लॉगिन सफल',
      'Invalid credentials': 'अमान्य क्रेडेंशियल'
    },
    'ta': {
      'Failed to authenticate': 'IBM Cloud உடன் அங்கீகாரம் தோல்வியடைந்தது',
      'Query field cannot': 'வினவல் புலம் காலியாக இருக்க முடியாது',
      'Invalid request format': 'தவறான கோரிக்கை வடிவம்',
      'Session cleared': 'அமர்வு வெற்றிகரமாக அழிக்கப்பட்டது',
      'Login successful': 'உள்நுழைவு வெற்றிகரமானது',
      'Invalid credentials': 'தவறான நற்சான்றிதழ்கள்'
    },
    'te': {
      'Failed to authenticate': 'IBM Cloud తో ప్రమాణీకరణ విఫలమైంది',
      'Query field cannot': 'ప్రశ్న ఫీల్డ్ ఖాళీగా ఉండకూడదు',
      'Invalid request format': 'చెల్లని అభ్యర్థన ఫార్మాట్',
      'Session cleared': 'సెషన్ విజయవంతంగా క్లియర్ చేయబడింది',
      'Login successful': 'లాగిన్ విజయవంతం',
      'Invalid credentials': 'చెల్లని ఆధారాలు'
    }
  };
  
  // Check if text matches any error message pattern
  const errorLang = errorTranslations[targetLanguage] || errorTranslations['en'];
  for (const [pattern, translation] of Object.entries(errorLang)) {
    if (text.includes(pattern)) {
      return translation;
    }
  }
  
  return text;
};

// Auto-translate alerts and dynamic content when language changes
function translateDynamicContent() {
  // Translate alert messages
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    if (alert.textContent.trim()) {
      alert.textContent = translateText(alert.textContent, currentLanguage);
    }
  });
  
  // Translate button text that wasn't caught by data-translate
  const buttons = document.querySelectorAll('button:not([data-translate])');
  buttons.forEach(button => {
    if (button.textContent.trim()) {
      button.textContent = translateText(button.textContent, currentLanguage);
    }
  });
}
