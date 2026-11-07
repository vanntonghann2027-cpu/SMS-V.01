# ការណែនាំអំពីការប្រើប្រាស់ PostgreSQL សម្រាប់ SMS-V.01
(PostgreSQL Setup Guide for Cambodian Student Management System)

ឯកសារ SQL Schema ពេញលេញមាននៅក្នុង: `database/schema.sql`

---

## ជម្រើសទី ១៖ ប្រើប្រាស់លើ Cloud ដោយឥតគិតថ្លៃ (Free 100% តាម Supabase) - ណែនាំបំផុត ⭐

**Supabase** ផ្តល់ជូននូវ **PostgreSQL Database** លើ Cloud ដោយឥតគិតថ្លៃ (Free Tier 500MB ដែលអាចផ្ទុកទិន្នន័យសិស្ស និងពិន្ទុបានរាប់ម៉ឺននាក់)។

### ជំហានអនុវត្ត៖
1. ចូលទៅកាន់គេហទំព័រ [https://supabase.com](https://supabase.com) រួចចុច **Start your project** (ចុះឈ្មោះដោយប្រើ Gmail ឬ GitHub)
2. បង្កើត Project ថ្មីមួយ (ឧ. ឈ្មោះ `sms-cambodia`) និងកំណត់ពាក្យសម្ងាត់ Database
3. នៅលើផ្ទាំង Dashboard ខាងឆ្វេងដៃ ចុចលើម៉ឺនុយ **SQL Editor**
4. ចុច **New query** រួច Copy កូដទាំងអស់ពីឯកសារ [`database/schema.sql`](schema.sql) យកទៅ Paste ចូល
5. ចុចប៊ូតុង **RUN** (ពណ៌បៃតង)
   - នោះតារាងទាំងអស់ (`academic_years`, `classes`, `subjects`, `students`, `scores`, `period_results`) ព្រមទាំងរូបមន្តគណនាចំណាត់ថ្នាក់ស្វ័យប្រវត្តិនឹងត្រូវបង្កើតឡើងភ្លាមៗ!
6. ចុចលើ **Project Settings** -> **API** ដើម្បីយក:
   - **Project URL**
   - **anon / public key**

---

## ជម្រើសទី ២៖ ដំណើរការ PostgreSQL នៅលើកុំព្យូទ័រផ្ទាល់ (Local Offline)

ប្រសិនបើលោកអ្នកចង់ដំណើរការក្នុងកុំព្យូទ័រផ្ទាល់ ឬម៉ាស៊ីនមេក្នុងសាលា (Local Server / Offline)៖

### នៅលើ macOS:
```bash
# ១. តម្លើង PostgreSQL តាមរយៈ Homebrew
brew install postgresql@16

# ២. ចាប់ផ្តើមសេវាកម្ម PostgreSQL
brew services start postgresql@16

# ៣. បង្កើត Database ឈ្មោះ sms_db
createdb sms_db

# ៤. រត់បញ្ចូល Schema
psql -d sms_db -f database/schema.sql
```

### នៅលើ Windows:
1. ទាញយក PostgreSQL Installer ពី [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)
2. តម្លើង និងបើកកម្មវិធី **pgAdmin 4**
3. បង្កើត Database ថ្មីឈ្មោះ `sms_db`
4. បើក **Query Tool** រួចបើកឯកសារ `schema.sql` ហើយចុច **Execute (F5)**។

---

## រចនាសម្ព័ន្ធតារាងក្នុង Database (Database Tables)

1. **`academic_years`** : ឆ្នាំសិក្សា (ឧ. ២០២៥-២០២៦, ២០២៦-២០២៧)
2. **`classes`** : កម្រិតថ្នាក់ទាំង ៨ (ថ្នាក់ទី៧ ដល់ ទី១២ វិទ្យាសាស្ត្រ និងសង្គម)
3. **`subjects`** : មុខវិជ្ជា ពិន្ទុពេញ (Max Score) និងមេគុណ (Coefficient)
4. **`students`** : អត្តលេខ គោត្តនាម-នាម ភេទ ថ្ងៃខែឆ្នាំកំណើត ទូរស័ព្ទ និងអាណាព្យាបាល
5. **`scores`** : ពិន្ទុជាក់ស្តែងតាមមុខវិជ្ជានីមួយៗ គាំទ្ររាល់ ២១ periods
6. **`period_results`** : សង្ខេបពិន្ទុសរុប មធ្យមភាគ ចំណាត់ថ្នាក់ និទ្ទេស (A-F) និងលទ្ធផល (ជាប់/ធ្លាក់)
