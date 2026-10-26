/** UI strings + starter questions for English, Thai, Vietnamese, Chinese, Hindi. */

export type Lang = "en" | "th" | "vi" | "zh" | "hi";
export type Collection = "hr_policies" | "tech_docs" | "product_docs";

export const LANGS: { id: Lang; label: string }[] = [
  { id: "en", label: "English" },
  { id: "th", label: "ไทย" },
  { id: "vi", label: "Tiếng Việt" },
  { id: "zh", label: "中文" },
  { id: "hi", label: "हिन्दी" },
];

export interface Dict {
  newChat: string; collection: string; history: string; knowledgeBase: string;
  upload: string; uploading: string; uploadHint: string;
  counts: (uploaded: number, builtin: number) => string;
  emptyTitle: string; emptySub: (col: string) => string; placeholder: (col: string) => string;
  fineprint: string; explainOn: string; explainOff: string; explainNotSetUp: string; explainTip: string;
  sources: string; searching: (col: string) => string; refused: (col: string) => string; injection: string;
  inPlain: string; verifying: string; checked: string; loose: string; backChecked: string; explainFailed: string;
  grounded: string; weak: string; blocked: string; traces: string; language: string;
  col: Record<Collection, string>;
}

export const I18N: Record<Lang, Dict> = {
  en: {
    newChat: "+ New chat", collection: "Collection", history: "History", knowledgeBase: "Knowledge base",
    upload: "⬆ Upload documents", uploading: "Uploading…", uploadHint: ".txt · .md · .csv · .pdf · up to 5 MB",
    counts: (u, b) => `${u} uploaded · ${b} built-in`,
    emptyTitle: "What can I help you find?",
    emptySub: (c) => `Searching ${c}. Every answer cites its sources, or is refused.`,
    placeholder: (c) => `Ask ${c}…`,
    fineprint: "Answers are grounded in retrieved sources. Enter to send · Shift+Enter for a new line",
    explainOn: "✨ Explain in plain words: on", explainOff: "✨ Explain in plain words: off",
    explainNotSetUp: "✨ Plain-words explanation: not set up",
    explainTip: "A free model re-explains each verified answer in your language and the result is checked against the sources.",
    sources: "Sources", searching: (c) => `Searching ${c}…`,
    refused: (c) => `I couldn't find a reliable answer to that in ${c}. Try rephrasing, or ask about something these documents cover:`,
    injection: "I can't help with that request.",
    inPlain: "✨ In plain words", verifying: "verifying against sources…", checked: "✓ checked against sources",
    loose: "⚠ loosely matches sources", backChecked: "✓ verified by back-translation",
    explainFailed: "I couldn't verify a plain-words explanation against the sources, so I'm not showing one. The sourced answer above is reliable.",
    grounded: "✓ Grounded", weak: "⚠ Weakly grounded", blocked: "⛔ Blocked: looks like a prompt-injection attempt",
    traces: "View trace reviewer →", language: "Language",
    col: { hr_policies: "HR Policies", tech_docs: "Tech Docs", product_docs: "Product Docs" },
  },
  th: {
    newChat: "+ แชทใหม่", collection: "คลังเอกสาร", history: "ประวัติ", knowledgeBase: "ฐานความรู้",
    upload: "⬆ อัปโหลดเอกสาร", uploading: "กำลังอัปโหลด…", uploadHint: ".txt · .md · .csv · .pdf · ไม่เกิน 5 MB",
    counts: (u, b) => `อัปโหลดแล้ว ${u} · ในระบบ ${b}`,
    emptyTitle: "ให้ช่วยค้นหาอะไรดี?",
    emptySub: (c) => `กำลังค้นหาใน ${c} ทุกคำตอบมีแหล่งอ้างอิง หากไม่มีหลักฐานจะปฏิเสธการตอบ`,
    placeholder: (c) => `ถามเกี่ยวกับ ${c}…`,
    fineprint: "คำตอบอ้างอิงจากแหล่งข้อมูลที่ค้นพบ · Enter เพื่อส่ง · Shift+Enter ขึ้นบรรทัดใหม่",
    explainOn: "✨ อธิบายแบบเข้าใจง่าย: เปิด", explainOff: "✨ อธิบายแบบเข้าใจง่าย: ปิด",
    explainNotSetUp: "✨ อธิบายแบบเข้าใจง่าย: ยังไม่ได้ตั้งค่า",
    explainTip: "โมเดลฟรีจะอธิบายคำตอบที่ตรวจสอบแล้วเป็นภาษาของคุณ และตรวจสอบกับแหล่งข้อมูลอีกครั้ง",
    sources: "แหล่งที่มา", searching: (c) => `กำลังค้นหาใน ${c}…`,
    refused: (c) => `ไม่พบคำตอบที่เชื่อถือได้ใน ${c} ลองเปลี่ยนวิธีถาม หรือถามเรื่องที่เอกสารเหล่านี้ครอบคลุม:`,
    injection: "ฉันไม่สามารถช่วยคำขอนี้ได้",
    inPlain: "✨ อธิบายง่าย ๆ", verifying: "กำลังตรวจสอบกับแหล่งข้อมูล…", checked: "✓ ตรวจสอบกับแหล่งข้อมูลแล้ว",
    loose: "⚠ ตรงกับแหล่งข้อมูลบางส่วน", backChecked: "✓ ตรวจสอบด้วยการแปลกลับแล้ว",
    explainFailed: "ไม่สามารถยืนยันคำอธิบายกับแหล่งข้อมูลได้ จึงไม่แสดง คำตอบที่มีแหล่งอ้างอิงด้านบนเชื่อถือได้",
    grounded: "✓ มีแหล่งอ้างอิง", weak: "⚠ อ้างอิงได้บางส่วน", blocked: "⛔ ถูกบล็อก: ดูเหมือนความพยายามแทรกคำสั่ง",
    traces: "เปิดหน้าตรวจสอบ trace →", language: "ภาษา",
    col: { hr_policies: "นโยบายบุคคล", tech_docs: "เอกสารเทคนิค", product_docs: "เอกสารผลิตภัณฑ์" },
  },
  vi: {
    newChat: "+ Cuộc trò chuyện mới", collection: "Bộ tài liệu", history: "Lịch sử", knowledgeBase: "Cơ sở kiến thức",
    upload: "⬆ Tải tài liệu lên", uploading: "Đang tải lên…", uploadHint: ".txt · .md · .csv · .pdf · tối đa 5 MB",
    counts: (u, b) => `${u} đã tải · ${b} có sẵn`,
    emptyTitle: "Tôi có thể giúp bạn tìm gì?",
    emptySub: (c) => `Đang tìm trong ${c}. Mọi câu trả lời đều dẫn nguồn, nếu không sẽ bị từ chối.`,
    placeholder: (c) => `Hỏi về ${c}…`,
    fineprint: "Câu trả lời dựa trên nguồn đã tìm thấy · Enter để gửi · Shift+Enter xuống dòng",
    explainOn: "✨ Giải thích dễ hiểu: bật", explainOff: "✨ Giải thích dễ hiểu: tắt",
    explainNotSetUp: "✨ Giải thích dễ hiểu: chưa thiết lập",
    explainTip: "Một mô hình miễn phí giải thích lại câu trả lời đã xác minh bằng ngôn ngữ của bạn và được kiểm tra lại với nguồn.",
    sources: "Nguồn", searching: (c) => `Đang tìm trong ${c}…`,
    refused: (c) => `Tôi không tìm thấy câu trả lời đáng tin cậy trong ${c}. Hãy thử diễn đạt lại, hoặc hỏi về nội dung các tài liệu này có:`,
    injection: "Tôi không thể hỗ trợ yêu cầu này.",
    inPlain: "✨ Nói đơn giản", verifying: "đang đối chiếu với nguồn…", checked: "✓ đã đối chiếu với nguồn",
    loose: "⚠ khớp một phần với nguồn", backChecked: "✓ đã xác minh bằng dịch ngược",
    explainFailed: "Tôi không thể xác minh phần giải thích với nguồn nên không hiển thị. Câu trả lời có dẫn nguồn ở trên là đáng tin cậy.",
    grounded: "✓ Có dẫn nguồn", weak: "⚠ Dẫn nguồn yếu", blocked: "⛔ Đã chặn: có dấu hiệu chèn lệnh (prompt injection)",
    traces: "Xem trình duyệt trace →", language: "Ngôn ngữ",
    col: { hr_policies: "Chính sách nhân sự", tech_docs: "Tài liệu kỹ thuật", product_docs: "Tài liệu sản phẩm" },
  },
  zh: {
    newChat: "+ 新对话", collection: "文档库", history: "历史", knowledgeBase: "知识库",
    upload: "⬆ 上传文档", uploading: "上传中…", uploadHint: ".txt · .md · .csv · .pdf · 最大 5 MB",
    counts: (u, b) => `已上传 ${u} · 内置 ${b}`,
    emptyTitle: "想查找什么？",
    emptySub: (c) => `正在检索「${c}」。每个回答都会标注来源，没有依据则拒绝回答。`,
    placeholder: (c) => `询问${c}…`,
    fineprint: "回答基于检索到的来源 · 按 Enter 发送 · Shift+Enter 换行",
    explainOn: "✨ 通俗解释：开", explainOff: "✨ 通俗解释：关",
    explainNotSetUp: "✨ 通俗解释：未设置",
    explainTip: "免费模型会用您的语言重新解释已验证的回答，并再次与来源核对。",
    sources: "来源", searching: (c) => `正在检索「${c}」…`,
    refused: (c) => `在「${c}」中没有找到可靠的答案。请换个问法，或询问这些文档涵盖的内容：`,
    injection: "我无法处理该请求。",
    inPlain: "✨ 通俗解释", verifying: "正在与来源核对…", checked: "✓ 已与来源核对",
    loose: "⚠ 与来源部分吻合", backChecked: "✓ 已通过回译验证",
    explainFailed: "无法将通俗解释与来源核实，因此不予显示。上方带来源的回答是可靠的。",
    grounded: "✓ 有来源依据", weak: "⚠ 依据较弱", blocked: "⛔ 已拦截：疑似提示词注入",
    traces: "查看追踪记录 →", language: "语言",
    col: { hr_policies: "人事政策", tech_docs: "技术文档", product_docs: "产品文档" },
  },
  hi: {
    newChat: "+ नई चैट", collection: "संग्रह", history: "इतिहास", knowledgeBase: "ज्ञान आधार",
    upload: "⬆ दस्तावेज़ अपलोड करें", uploading: "अपलोड हो रहा है…", uploadHint: ".txt · .md · .csv · .pdf · अधिकतम 5 MB",
    counts: (u, b) => `${u} अपलोड · ${b} पहले से`,
    emptyTitle: "मैं आपको क्या खोजने में मदद करूँ?",
    emptySub: (c) => `${c} में खोज रहा हूँ। हर उत्तर में स्रोत दिए जाते हैं, अन्यथा उत्तर देने से मना कर दिया जाता है।`,
    placeholder: (c) => `${c} के बारे में पूछें…`,
    fineprint: "उत्तर खोजे गए स्रोतों पर आधारित हैं · भेजने के लिए Enter · नई पंक्ति के लिए Shift+Enter",
    explainOn: "✨ सरल शब्दों में समझाएँ: चालू", explainOff: "✨ सरल शब्दों में समझाएँ: बंद",
    explainNotSetUp: "✨ सरल व्याख्या: सेट नहीं है",
    explainTip: "एक मुफ़्त मॉडल सत्यापित उत्तर को आपकी भाषा में समझाता है और उसे फिर से स्रोतों से जाँचा जाता है।",
    sources: "स्रोत", searching: (c) => `${c} में खोज रहा हूँ…`,
    refused: (c) => `${c} में मुझे इसका भरोसेमंद उत्तर नहीं मिला। प्रश्न दूसरे ढंग से पूछें, या ऐसी बात पूछें जो इन दस्तावेज़ों में है:`,
    injection: "मैं इस अनुरोध में मदद नहीं कर सकता।",
    inPlain: "✨ सरल शब्दों में", verifying: "स्रोतों से जाँच हो रही है…", checked: "✓ स्रोतों से जाँचा गया",
    loose: "⚠ स्रोतों से आंशिक मेल", backChecked: "✓ वापसी-अनुवाद से सत्यापित",
    explainFailed: "मैं इस व्याख्या को स्रोतों से सत्यापित नहीं कर सका, इसलिए नहीं दिखा रहा। ऊपर का स्रोत-सहित उत्तर विश्वसनीय है।",
    grounded: "✓ स्रोत-आधारित", weak: "⚠ कमज़ोर आधार", blocked: "⛔ रोका गया: प्रॉम्प्ट इंजेक्शन जैसा प्रयास",
    traces: "ट्रेस रिव्यूअर देखें →", language: "भाषा",
    col: { hr_policies: "एचआर नीतियाँ", tech_docs: "तकनीकी दस्तावेज़", product_docs: "उत्पाद दस्तावेज़" },
  },
};

export const STARTERS: Record<Lang, Record<Collection, string[]>> = {
  en: {
    hr_policies: ["How much PTO do I get per year?", "What is the parental leave policy?", "How do I submit an expense report?"],
    tech_docs: ["How do I authenticate to the API gateway?", "Where do I find the deployment runbook?", "What's the SLA for the search service?"],
    product_docs: ["How do I export data to CSV?", "What's new in this release?", "How do I invite a teammate?"],
  },
  th: {
    hr_policies: ["ฉันได้วันลาพักร้อนกี่วันต่อปี", "ลาเลี้ยงดูบุตรได้กี่สัปดาห์"],
    tech_docs: ["ยืนยันตัวตนกับ API gateway อย่างไร"],
    product_docs: ["ส่งออกข้อมูลเป็น CSV อย่างไร"],
  },
  vi: {
    hr_policies: ["Tôi được nghỉ phép bao nhiêu ngày mỗi năm?", "Nghỉ thai sản được bao nhiêu tuần?"],
    tech_docs: ["Làm sao xác thực với API gateway?"],
    product_docs: ["Làm thế nào để xuất dữ liệu ra CSV?"],
  },
  zh: {
    hr_policies: ["我每年有多少天带薪休假？", "育儿假有几周？"],
    tech_docs: ["如何向 API 网关认证？"],
    product_docs: ["如何导出 CSV？"],
  },
  hi: {
    hr_policies: ["मुझे प्रति वर्ष कितने दिन की छुट्टी मिलती है?", "अभिभावक अवकाश कितने सप्ताह का है?"],
    tech_docs: ["API गेटवे से प्रमाणीकरण कैसे करें?"],
    product_docs: ["डेटा CSV में कैसे निर्यात करें?"],
  },
};

export function detectUiLang(): Lang {
  if (typeof navigator === "undefined") return "en";
  const l = navigator.language.toLowerCase();
  if (l.startsWith("th")) return "th";
  if (l.startsWith("vi")) return "vi";
  if (l.startsWith("zh")) return "zh";
  if (l.startsWith("hi")) return "hi";
  return "en";
}
