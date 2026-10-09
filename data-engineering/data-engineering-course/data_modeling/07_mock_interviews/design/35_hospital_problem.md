# Lesson 35 — Practice: Hospital Patient Records

> **Format:** problem statement. Time-box: 30 minutes.
> Read the prompt, draw the schema, then read the
> solution in [`code/solutions.py`](../code/solutions.py).

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## The prompt

Design a data warehouse for a **hospital patient
records** system. The hospital admits patients,
performs procedures, prescribes medications, and
discharges. The hospital wants to report on:

1. **Patient flow** — admissions per day, average
   length of stay, readmission rate.
2. **Procedure volumes** — which procedures are
   performed, by which surgeon, with what outcomes.
3. **Medication usage** — which drugs are
   prescribed, in what combinations, with what
   side-effect rates.
4. **Outcomes** — mortality, complications,
   readmission within 30 days.
5. **Billing** — total charges, by payer, by
   procedure.

The OLTP source tracks: patients (id, name, dob,
gender, insurance), admissions (admission_id,
patient_id, admit_date, discharge_date, ward),
procedures (procedure_id, admission_id, surgeon_id,
procedure_code, date, outcome), medications
(med_id, admission_id, drug_code, dose, start,
end), diagnoses (diagnosis_id, admission_id,
icd_code, primary_flag), and surgeons (id, name,
specialty).

The data has **strong privacy requirements** (HIPAA
in the US). All queries must support row-level
access control and de-identification for
analytics.

---

## What to produce

1. **Discovery questions** — at least five.
2. **Requirements doc** — consumers, use cases,
   sources, and key facts. Note the privacy
   requirements.
3. **Star schema** — fact tables, dimensions, grain.
4. **SCD choices** — for each dim.
5. **Three SQL queries** — average LOS, readmission
   rate, top procedures.
6. **Tradeoffs** — at least two.

---

## Hints

- An admission is a *lifecycle* — admit to
  discharge — with procedures and medications
  happening during it. That's an *accumulating
  snapshot* fact, not a transactional fact.
- A procedure is also a discrete event with a
  surgeon and an outcome. Could be its own
  transactional fact.
- A diagnosis is a *classification* of an admission.
  Could be a dim attribute, but ICD codes are
  usually modeled as a factless fact (a diagnosis
  happened) because a patient can have many
  diagnoses per admission.
- Patient identity is the most sensitive part. The
  dim should be tokenized — store a surrogate
  `patient_key` and a separate, restricted mapping
  table for the natural `patient_id`.
- Diagnoses and procedures are often coded
  (ICD-10, CPT). The codes are slow-changing
  classification systems, but the *attributes* on
  each code (description, category) change
  yearly.

---

## Sample discovery questions

1. Is the grain "one row per admission" or "one
   row per procedure / medication / diagnosis"? I
   suspect multiple facts.
2. Can a patient have multiple open admissions at
   once? (Usually no, but worth confirming.)
3. Is "readmission within 30 days" defined as the
   next admission starting within 30 days of the
   last discharge?
4. Are diagnoses primary vs secondary? (ICD codes
   often have a `primary_flag`.)
5. Is the data refreshed in real-time (HL7 feed) or
   in batch?
6. What is the retention requirement? Hospital data
   is often kept 7–10 years.
7. Are there de-identification requirements for
   analytics? E.g., the analyst sees age in years,
   not DOB.
8. Are surgeons employees or contractors? (Affects
   whether they're a "conformed" dim shared with
   the procedures fact only, or also with the
   medication fact.)
9. Are outcomes (mortality, complications) coded
   in a standard way, or is it free-text from the
   surgeon?
10. What is the SLA for the warehouse? Clinical
    decisions may need real-time; reporting can be
    daily.

---

## Sample star schema

```
fact_admissions (accumulating snapshot)
   grain: one row per admission
   measures: los_days, procedure_count, medication_count, total_charges
   milestones: admit_date_key, procedure_date_key, discharge_date_key
   dimensions:
     dim_patient   (SCD 2; tokenized; attributes: age_band, gender, insurance_type, region)
     dim_ward      (SCD 1; attributes: ward_name, type, floor)
     dim_diagnosis (junk or SCD 1; icd_code, description, category)
     dim_date      (conformed; role-played)

fact_procedures (transactional)
   grain: one row per procedure performed
   measures: duration_min, complication_flag, mortality_flag
   dimensions:
     dim_patient, dim_surgeon, dim_procedure_code, dim_date

fact_medications (transactional)
   grain: one row per medication administered
   measures: dose_mg, duration_days
   dimensions:
     dim_patient, dim_drug, dim_prescriber, dim_date

fact_diagnoses (factless)
   grain: one row per (admission, diagnosis)
   measures: primary_flag (degenerate)
   dimensions:
     dim_patient, dim_diagnosis_code, dim_admission
```

`dim_patient` is shared across all facts. The
patient dim is tokenized — `patient_key` is a
surrogate, and the natural `patient_id` is in a
restricted mapping table that only the ETL has
access to.

---

## Sample SQL queries

**Average length of stay by ward:**

```sql
SELECT w.ward_name,
       AVG(f.los_days) AS avg_los,
       COUNT(*) AS admissions
FROM fact_admissions f
JOIN dim_ward w ON f.ward_key = w.ward_key
WHERE f.discharge_date_key IS NOT NULL
GROUP BY w.ward_name;
```

**30-day readmission rate:**

```sql
WITH next_admit AS (
  SELECT a.patient_key, a.discharge_date_key,
         LEAD(a.admit_date_key) OVER (
           PARTITION BY a.patient_key
           ORDER BY a.admit_date_key
         ) AS next_admit_date_key
  FROM fact_admissions a
  WHERE a.discharge_date_key IS NOT NULL
)
SELECT 100.0 * SUM(CASE WHEN next_admit_date_key - discharge_date_key <= 30
                        THEN 1 ELSE 0 END) / COUNT(*) AS readmit_30d_pct
FROM next_admit;
```

**Top 10 procedures:**

```sql
SELECT p.cpt_code, p.description, COUNT(*) AS n
FROM fact_procedures f
JOIN dim_procedure_code p ON f.procedure_code_key = p.procedure_code_key
WHERE f.procedure_date_key BETWEEN 20240101 AND 20241231
GROUP BY p.cpt_code, p.description
ORDER BY n DESC
LIMIT 10;
```

---

## Tradeoffs to call out

1. **Accumulating snapshot vs transactional for
   admissions.** I picked accumulating snapshot
   because admission has clear milestones (admit,
   first procedure, discharge) and we want to know
   "how long did the admission last" as a stored
   measure. Transactional would require us to
   recompute LOS at query time.
2. **Tokenized patient dim vs natural key.** I
   picked tokenized because HIPAA requires
   de-identification for analytics. Cost: the
   mapping table is a security liability and a
   bottleneck. Worth it.
3. **Procedures as a separate fact vs as measures
   on the admission fact.** I picked separate
   because a single admission can have many
   procedures, and putting them on the admission
   fact would require an array column or a wide
   table with `procedure_1`, `procedure_2`, etc.
4. **SCD 2 on patient.** Required for historical
   attribution (a patient who changes insurance
   should attribute Q1 procedures to Q1
   insurance).

---

## Try it

Set a 30-minute timer. Work the problem cold. Then
read [`code/solutions.py`](../code/solutions.py) and
[`tests/test_solutions.py`](../tests/test_solutions.py).

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
