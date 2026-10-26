# Section 1 Quiz — Introduction to EC2

> 8 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you have attempted the question.
> **Pass bar: 5 / 8.**

---

**1. What does EC2 stand for, and what does the service provide?**

- A) Elastic Container Cloud — a managed Kubernetes service
- B) Elastic Compute Cloud — resizable virtual server capacity in the AWS cloud
- C) Elastic Cache Cluster — a managed in-memory cache
- D) Elastic Cloud Compute — a serverless function runtime

<details><summary>Show answer</summary>

**B) Elastic Compute Cloud — resizable virtual server capacity in the AWS cloud.** EC2 is AWS's flagship virtual-server service. It lets you launch VM instances on demand, scale them up or down, and pay only for what you use. (A) is EKS, (C) is ElastiCache, (D) is a distractor.

</details>

---

**2. How many sections and how many lectures does this course have?**

- A) 6 sections, 24 lectures
- B) 8 sections, 38 lectures
- C) 10 sections, 50 lectures
- D) 12 sections, 60 lectures

<details><summary>Show answer</summary>

**B) 8 sections, 38 lectures.** The course is intentionally short and focused: 8 sections, 38 lectures, 6 working boto3 demos, 5 architecture diagrams, 8 quizzes.

</details>

---

**3. Which of the following is one of the three load balancers covered in this course?**

- A) Classic Load Balancer (CLB)
- B) Network Load Balancer (NLB)
- C) Database Load Balancer (DLB)
- D) Front Door Load Balancer (FDLB)

<details><summary>Show answer</summary>

**B) Network Load Balancer (NLB).** The three load balancers covered are the Network Load Balancer (NLB, Layer 4, section 6), the Application Load Balancer (ALB, Layer 7, section 7), and the Gateway Load Balancer (GWLB, third-party appliances, section 8). The Classic Load Balancer (CLB) is a deprecated AWS service that the course does not cover.

</details>

---

**4. Which EC2 pricing model is intended for fault-tolerant, stateless workloads and offers the largest discount over on-demand?**

- A) On-Demand Instances
- B) Reserved Instances
- C) Savings Plans
- D) Spot Instances

<details><summary>Show answer</summary>

**D) Spot Instances.** Spot Instances let you bid on spare EC2 capacity at up to 90% off the on-demand price, but AWS can reclaim them with two minutes' notice — so they are safe only for fault-tolerant, stateless workloads. Reserved Instances and Savings Plans also offer significant discounts (up to ~70%) but require a 1- or 3-year commitment and are intended for steady-state workloads.

</details>

---

**5. What does the `moto` library do, and why is it relevant to this course?**

- A) It is a metrics tool for CloudWatch
- B) It is a Python library that mocks the AWS API, so boto3 scripts can run without an AWS account
- C) It is a deployment tool for EC2 instances
- D) It is a replacement for the AWS CLI

<details><summary>Show answer</summary>

**B) It is a Python library that mocks the AWS API, so boto3 scripts can run without an AWS account.** Every boto3 script in this course is `moto`-mockable, which means you can complete the entire course on a laptop with no AWS account and no internet connection. The same scripts run unchanged against a real AWS account when you are ready.

</details>

---

**6. Which AWS certification exam explicitly tests EC2 and Elastic Load Balancing knowledge?**

- A) AWS Cloud Practitioner (CLF-C02) only
- B) AWS Solutions Architect Associate (SAA-C03) only
- C) AWS Solutions Architect Professional (SAP-C02) only
- D) All three: Cloud Practitioner, Solutions Architect Associate, and Solutions Architect Professional

<details><summary>Show answer</summary>

**D) All three: Cloud Practitioner, Solutions Architect Associate, and Solutions Architect Professional.** EC2 and ELB are foundational services and are tested on every AWS certification from Foundational through Professional. Section 1's "Who This Course Is For" lecture calls this out as one of the three target personas.

</details>

---

**7. Which of the following is the correct mapping of load balancer to the OSI layer at which it primarily operates?**

- A) NLB operates at Layer 7, ALB at Layer 4, GWLB at Layer 3
- B) NLB operates at Layer 4, ALB at Layer 7, GWLB at Layer 3
- C) NLB operates at Layer 3, ALB at Layer 4, GWLB at Layer 7
- D) All three load balancers operate at Layer 7

<details><summary>Show answer</summary>

**B) NLB operates at Layer 4 (Transport), ALB at Layer 7 (Application), GWLB at Layer 3 (Network).** The Network Load Balancer forwards TCP/UDP without inspecting payloads. The Application Load Balancer understands HTTP and HTTPS and supports host- and path-based routing. The Gateway Load Balancer operates at Layer 3 and is used to deploy fleets of third-party virtual appliances (firewalls, IDS, DPI).

</details>

---

**8. According to L01, which of these is NOT one of the design decisions called out for the course?**

- A) Every code sample is `moto`-mockable so the course can be done offline
- B) The course is intentionally short — 38 lectures averaging about three minutes each
- C) The course focuses exclusively on serverless and does not cover EC2 instance management
- D) The three load-balancer sections (NLB, ALB, GWLB) operate at different network layers and solve different problems

<details><summary>Show answer</summary>

**C) The course focuses exclusively on serverless and does not cover EC2 instance management.** This is the opposite of what L01 says. The course is centered on EC2 — instance management is covered in section 5 (L23–L26) and is a core part of the syllabus. (A), (B), and (D) are all design decisions called out explicitly in L01.

</details>
