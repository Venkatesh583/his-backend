# Database Schema → Model Mapping

This document maps the SQLite tables to suggested ORM-style models (names and fields).

- PlanCategory
  - category_id: Integer (PK)
  - category_name: String
  - active_sw: Char
  - create_date: Date
  - update_date: Date
  - created_by: String
  - updated_by: String

- PlanMaster
  - plan_id: Integer (PK)
  - plan_name: String
  - plan_start_date: Date
  - plan_end_date: Date
  - plan_category_id: Integer (FK -> PlanCategory)
  - active_sw: Char
  - create_date: Date
  - update_date: Date
  - created_by: String
  - updated_by: String

- CaseWorkerAcct
  - acc_id: Integer (PK)
  - fullname: String
  - email: String
  - pwd: String
  - phno: String
  - gender: Char
  - ssn: String
  - dob: Date
  - active_sw: Char
  - create_date: Date
  - update_date: Date

- CitizenApp
  - app_id: Integer (PK)
  - fullname: String
  - email: String
  - phno: String
  - ssn: String
  - gender: Char
  - state_name: String
  - create_date: Date
  - update_date: Date

- DCCase
  - case_id: Integer (PK)
  - case_num: Integer (unique)
  - app_id: Integer (FK -> CitizenApp)
  - plan_id: Integer (FK -> PlanMaster)

- DCIncome
  - income_id: Integer (PK)
  - case_num: Integer (FK -> DCCase.case_num)
  - emp_income: Decimal
  - property_income: Decimal

- DCChildren
  - children_id: Integer (PK)
  - case_num: Integer
  - children_dob: Date
  - children_ssn: String

- DCEducation
  - edu_id: Integer (PK)
  - case_num: Integer
  - highest_qualification: String
  - graduation_year: Integer

- EligDtls
  - elig_id: Integer (PK)
  - case_num: Integer
  - plan_name: String
  - plan_status: String
  - plan_start_date: Date
  - plan_end_date: Date
  - benefit_amt: Decimal
  - denial_reason: String
  - create_date: Date

- CoTriggers
  - trg_id: Integer (PK)
  - case_num: Integer
  - trg_status: Char
  - notice: Text
  - create_date: Date
  - update_date: Date

## Missing / Suggested Endpoints

- Application create page: `POST /public/register` (exists)
- Application status search API: `GET /application-status-search` (MISSING)
- Create-application route used in some templates: `/create-application` (MISSING or alias to `/public/register`)
- Admin: endpoints to manage caseworkers (create/update) — UI exists but no POST API to add caseworkers (MISSING)
- Download notice endpoint alias used in templates: `/download-notice/<app_id>` — app uses `/generate-notice/<app_id>` (mismatch)

Recommendation: add small route `GET /application-status-search` to lookup `app_id` and redirect to `/application/<app_id>/status`. Add aliases or update templates to use `/generate-notice/<app_id>` consistently.
