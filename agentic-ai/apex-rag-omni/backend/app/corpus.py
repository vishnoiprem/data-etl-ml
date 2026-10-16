"""Built-in demo corpus (synthetic, safe to ship).

One list of (doc_id, title, text) per collection. This is what the local
retriever indexes so the app answers real questions with zero infra.
Swap in Qdrant/ES by setting APEX_RETRIEVER=remote (see apex_retriever).
"""
from __future__ import annotations

CORPUS: dict[str, list[tuple[str, str, str]]] = {
    "hr_policies": [
        ("hr-pto-001", "PTO Policy §1 Accrual",
         "Full-time employees accrue 20 days of paid time off (PTO) per calendar year. "
         "PTO accrues monthly at 1.67 days. Part-time employees accrue PTO pro rata to their contracted hours."),
        ("hr-pto-002", "PTO Policy §2 Carryover",
         "Up to 5 unused PTO days may be carried over into the next calendar year. "
         "Carried-over days expire on 31 March. PTO is not paid out except where required by law."),
        ("hr-pto-003", "PTO Policy §3 Requesting time off",
         "Request PTO in the HR portal at least 5 working days ahead. Requests longer than 10 consecutive days "
         "need approval from your manager and your HR business partner."),
        ("hr-leave-001", "Parental Leave Policy",
         "Primary caregivers receive 16 weeks of fully paid parental leave. Secondary caregivers receive 6 weeks. "
         "Leave may start up to 4 weeks before the expected birth or placement and must be taken within 12 months."),
        ("hr-leave-002", "Sick Leave Policy",
         "Employees receive 10 paid sick days per year. A medical certificate is required for absences longer than "
         "3 consecutive days. Notify your manager before your shift starts."),
        ("hr-exp-001", "Expense Reports",
         "Submit expense reports in the finance portal within 30 days of the expense. Attach itemised receipts for "
         "every claim over 25 USD. Reimbursement is paid in the next monthly payroll run."),
        ("hr-exp-002", "Travel Policy",
         "Book economy class for flights under 6 hours. Hotel stays are capped at 150 USD per night in standard "
         "cities and 220 USD in high-cost cities. Travel must be pre-approved by your manager."),
        ("hr-ben-001", "Health Benefits",
         "Health, dental and vision insurance start on your first day. The company covers 80 percent of the "
         "employee premium and 50 percent of dependant premiums. Open enrolment runs every November."),
        ("hr-ben-002", "Retirement Plan",
         "The company matches 100 percent of retirement contributions up to 4 percent of salary. "
         "Matching contributions vest after 2 years of service."),
        ("hr-conduct-001", "Code of Conduct",
         "All employees must treat colleagues with respect and report harassment or discrimination to HR or the "
         "anonymous ethics line. Retaliation against anyone who reports in good faith is prohibited."),
        # ---- multilingual demo passages (th / vi / zh / hi) ----
        ("hr-pto-001-th", "นโยบายวันลาพักร้อน (PTO) ข้อ 1 การสะสมวันลา",
         "พนักงานประจำเต็มเวลามีสิทธิ์ลาพักร้อนแบบได้รับค่าจ้าง (PTO) 20 วันต่อปีปฏิทิน วันลาพักร้อนสะสมเดือนละ 1.67 วัน "
         "พนักงานพาร์ทไทม์สะสมวันลาตามสัดส่วนชั่วโมงทำงานตามสัญญา"),
        ("hr-pto-001-vi", "Chính sách nghỉ phép (PTO) §1 Tích lũy",
         "Nhân viên toàn thời gian được tích lũy 20 ngày nghỉ phép có lương (PTO) mỗi năm dương lịch. PTO được tích lũy hàng tháng với 1,67 ngày. "
         "Nhân viên bán thời gian tích lũy theo tỷ lệ số giờ làm việc theo hợp đồng."),
        ("hr-pto-001-zh", "带薪休假（PTO）政策 第1条 累计",
         "全职员工每个日历年享有20天带薪休假（PTO）。PTO按月累计，每月累计1.67天。兼职员工按合同工时比例累计带薪休假。"),
        ("hr-pto-001-hi", "PTO नीति धारा 1: अवकाश जमा होना",
         "पूर्णकालिक कर्मचारियों को प्रति कैलेंडर वर्ष 20 दिन का सवेतन अवकाश (PTO) मिलता है। PTO हर महीने 1.67 दिन की दर से जमा होता है। "
         "अंशकालिक कर्मचारियों का PTO उनके अनुबंधित घंटों के अनुपात में जमा होता है।"),
        ("hr-leave-001-th", "นโยบายลาเลี้ยงดูบุตร",
         "ผู้ดูแลหลักได้รับลาเลี้ยงดูบุตรโดยได้รับค่าจ้างเต็มจำนวน 16 สัปดาห์ ผู้ดูแลรองได้รับ 6 สัปดาห์ "
         "สามารถเริ่มลาได้ล่วงหน้าไม่เกิน 4 สัปดาห์ก่อนวันกำหนดคลอดหรือรับเด็ก และต้องใช้สิทธิ์ภายใน 12 เดือน"),
        ("hr-leave-001-vi", "Chính sách nghỉ thai sản và chăm con",
         "Người chăm sóc chính được nghỉ hưởng nguyên lương 16 tuần. Người chăm sóc phụ được nghỉ 6 tuần. "
         "Kỳ nghỉ có thể bắt đầu sớm nhất 4 tuần trước ngày dự sinh hoặc nhận con nuôi và phải sử dụng trong vòng 12 tháng."),
        ("hr-leave-001-zh", "育儿假政策",
         "主要照顾者享有16周全薪育儿假，次要照顾者享有6周。育儿假最早可在预产期或收养前4周开始，并须在12个月内休完。"),
        ("hr-leave-001-hi", "अभिभावक अवकाश नीति",
         "प्राथमिक देखभालकर्ता को 16 सप्ताह का पूर्ण वेतन सहित अवकाश मिलता है। द्वितीयक देखभालकर्ता को 6 सप्ताह मिलते हैं। "
         "अवकाश अपेक्षित जन्म या गोद लेने से अधिकतम 4 सप्ताह पहले शुरू हो सकता है और 12 महीनों के भीतर लेना होगा।"),
    ],
    "tech_docs": [
        ("tech-auth-001", "API Gateway Authentication",
         "Authenticate to the API gateway by sending your key in the X-API-Key header. Keys are issued per service "
         "in the developer portal and rotate every 90 days. Requests without a valid key return HTTP 403."),
        ("tech-auth-002", "Rotating API Keys",
         "To rotate a key, create a new key in the developer portal, deploy it, then revoke the old key. "
         "Both keys are valid during the 24 hour overlap window."),
        ("tech-deploy-001", "Deployment Runbook",
         "Deployments run through the CI pipeline. Merge to main triggers a build, then a canary deploy to 5 percent "
         "of traffic for 15 minutes. Promote to 100 percent only if the error rate stays below 1 percent."),
        ("tech-deploy-002", "Rollback Procedure",
         "To roll back, run the rollback job in the CI pipeline with the previous release tag. Rollbacks complete in "
         "under 5 minutes. Page the on-call engineer if the rollback fails."),
        ("tech-sla-001", "Search Service SLA",
         "The search service targets 99.9 percent monthly availability and a p95 latency under 500 ms. "
         "Breaches are reported in the weekly reliability review."),
        ("tech-rate-001", "Rate Limits",
         "Each API key is limited to 60 requests per second. Exceeding the limit returns HTTP 429 with a "
         "Retry-After header. Contact the platform team to raise a limit."),
        ("tech-oncall-001", "On-call Escalation",
         "Page the primary on-call engineer first. If there is no acknowledgement within 10 minutes, the page "
         "escalates to the secondary and then the engineering manager."),
        ("tech-log-001", "Logging Standards",
         "Services emit structured JSON logs that include a request_id. Never log secrets, API keys or personal data. "
         "Logs are retained for 30 days."),
        # ---- multilingual demo passages (th / vi / zh / hi) ----
        ("tech-auth-001-th", "การยืนยันตัวตนของ API Gateway",
         "ยืนยันตัวตนกับ API gateway โดยส่งคีย์ของคุณในส่วนหัว X-API-Key คีย์ออกให้ต่อบริการในพอร์ทัลนักพัฒนาและหมุนเวียนทุก 90 วัน "
         "คำขอที่ไม่มีคีย์ที่ถูกต้องจะได้รับ HTTP 403"),
        ("tech-auth-001-vi", "Xác thực API Gateway",
         "Xác thực với API gateway bằng cách gửi khóa của bạn trong tiêu đề X-API-Key. Khóa được cấp cho từng dịch vụ trong cổng nhà phát triển và được xoay vòng mỗi 90 ngày. "
         "Yêu cầu không có khóa hợp lệ sẽ nhận HTTP 403."),
        ("tech-auth-001-zh", "API 网关认证",
         "通过在 X-API-Key 请求头中发送密钥来向 API 网关认证。密钥在开发者门户中按服务签发，每 90 天轮换一次。没有有效密钥的请求将返回 HTTP 403。"),
        ("tech-auth-001-hi", "API गेटवे प्रमाणीकरण",
         "अपनी कुंजी को X-API-Key हेडर में भेजकर API गेटवे से प्रमाणीकरण करें। कुंजियाँ डेवलपर पोर्टल में प्रति सेवा जारी की जाती हैं और हर 90 दिन में बदली जाती हैं। "
         "मान्य कुंजी के बिना अनुरोधों को HTTP 403 मिलता है।"),
    ],
    "product_docs": [
        ("prod-export-001", "Exporting Data to CSV",
         "To export data to CSV, open the report, choose Export, then select CSV. Exports are limited to 100,000 rows; "
         "larger exports are emailed as a download link."),
        ("prod-invite-001", "Inviting Teammates",
         "Admins can invite teammates from Settings, then Members, then Invite. Invited users get an email link that "
         "expires after 7 days. Members can be assigned the Viewer, Editor or Admin role."),
        ("prod-release-001", "Release 4.2 Highlights",
         "Release 4.2 adds scheduled reports, a dark theme, and faster dashboard loading. Scheduled reports can be "
         "emailed daily or weekly in PDF or CSV format."),
        ("prod-release-002", "Release 4.1 Highlights",
         "Release 4.1 introduced single sign-on with SAML, audit logs for admins, and bulk user import from CSV."),
        ("prod-sso-001", "Single Sign-On Setup",
         "Enable SAML single sign-on under Settings, then Security. Provide your identity provider metadata URL and "
         "test the connection before enforcing SSO for all members."),
        ("prod-limits-001", "Plan Limits",
         "The Free plan includes 3 members and 1,000 records. The Team plan includes 25 members and 100,000 records. "
         "Enterprise plans have custom limits."),
        ("prod-api-001", "Public API",
         "The public REST API supports reading and writing records. Create a token under Settings, then Developer. "
         "Tokens are scoped read-only or read-write."),
        # ---- multilingual demo passages (th / vi / zh / hi) ----
        ("prod-export-001-th", "การส่งออกข้อมูลเป็น CSV",
         "หากต้องการส่งออกข้อมูลเป็น CSV ให้เปิดรายงาน เลือกส่งออก แล้วเลือก CSV การส่งออกจำกัดที่ 100,000 แถว "
         "หากมากกว่านั้นระบบจะส่งลิงก์ดาวน์โหลดทางอีเมล"),
        ("prod-export-001-vi", "Xuất dữ liệu ra CSV",
         "Để xuất dữ liệu ra CSV, hãy mở báo cáo, chọn Xuất, rồi chọn CSV. Giới hạn xuất là 100,000 dòng; các lần xuất lớn hơn sẽ được gửi qua email dưới dạng liên kết tải xuống."),
        ("prod-export-001-zh", "导出数据为 CSV",
         "要将数据导出为 CSV，请打开报表，选择“导出”，再选择 CSV。导出上限为 100,000 行；更大的导出会以下载链接的形式通过邮件发送。"),
        ("prod-export-001-hi", "डेटा को CSV में निर्यात करना",
         "डेटा को CSV में निर्यात करने के लिए रिपोर्ट खोलें, निर्यात चुनें, फिर CSV चुनें। निर्यात 100,000 पंक्तियों तक सीमित है; "
         "बड़े निर्यात डाउनलोड लिंक के रूप में ईमेल किए जाते हैं।"),
    ],
}
