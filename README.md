# SMS v0.1 - ប្រព័ន្ធគ្រប់គ្រងពិន្ទុសិស្ស (Student Management System)

ប្រព័ន្ធគ្រប់គ្រងពិន្ទុ និងការប្រឡងរបស់សិស្សានុសិស្ស គាំទ្រទាំងលើកុំព្យូទ័រ (Desktop) និងទូរស័ព្ទដៃ/Tablet (PWA Mobile App)។

## 📱 មុខងារពិសេសលើទូរស័ព្ទដៃ & Tablet (Mobile App)
- **បញ្ចូលពិន្ទុតាមអក្សរសម្ងាត់ (Secret Code)**៖ ផ្ទៀងផ្ទាត់ដោយស្វ័យប្រវត្តិតាមកម្រិតថ្នាក់ក្នុងខែប្រឡង Active។
- **បញ្ចូលតាមសម្លេង AI (Voice AI)**៖ គាំទ្រភាសាខ្មែរ (`km-KH`) តាមរយៈ Web Speech API និង Google AI Studio (Gemini 2.5 Flash)។
- **Touch Numpad លឿនរហ័ស**៖ វាយលេខ ១ ដល់ ២ ខ្ទង់លោតដោយស្វ័យប្រវត្តិ (ចុច `A` = `0` សិស្សអវត្តមាន)។
- **គាំទ្រ Tablet External Keyboard**៖ ចុច `Enter` ឬ `↓` ដើម្បីរំកិលទៅសិស្សបន្ទាប់ភ្លាមៗ។
- **Cloud & Local LAN Sync**៖ Sync ពិន្ទុទៅ Supabase Cloud PostgreSQL និង local server ដោយស្វ័យប្រវត្តិ។
- **PWA (Progressive Web App)**៖ អាចដំឡើងលើ Home Screen (iPhone Safari & Android Chrome) ដំណើរការពេញអេក្រង់ (Full Screen) ដូច Native App។

## 💻 មុខងារលើកុំព្យូទ័រ (Desktop Dashboard)
- រៀបចំតុ និងបន្ទប់ប្រឡងតាមកម្រិតថ្នាក់។
- បង្កើត និងបោះពុម្ពម៉ាទ្រីសអក្សរសម្ងាត់ (Secret Matrix)។
- បញ្ចូលពិន្ទុតាមមុខវិជ្ជា និងគណនាចំណាត់ថ្នាក់ និទ្ទេស (A, B, C, D, E, F)។
- បោះពុម្ពតារាងកិត្តិយស ព្រឹត្តិបត្រពិន្ទុ និងតារាងសរុបប្រចាំខែ/ឆមាស/ឆ្នាំ។
- Backup ទិន្នន័យជា SQLite `.db` និង JSON ដោយស្វ័យប្រវត្តិ។

## 🚀 របៀបដំណើរការ (Getting Started)

### ១. ដំណើរការ Local Server
```bash
python3 server.py
```
- បើក Dashboard លើកុំព្យូទ័រ៖ `http://localhost:8080`
- បើកលើទូរស័ព្ទដៃ/Tablet ក្នុងបណ្តាញ Wi-Fi តែមួយ៖ `http://<IP_កុំព្យូទ័រ>:8080/mobile.html`

### ២. ការដំឡើង App លើទូរស័ព្ទ (PWA)
- **iPhone / iPad**៖ បើក Safari -> ចុចប៊ូតុង Share (📤) -> ជ្រើសរើស **«Add to Home Screen»**
- **Android**៖ បើក Chrome -> ចុច Menu (⋮) -> ជ្រើសរើស **«Install App»** ឬ **«Add to Home Screen»**

