/**
 * Default text of the live /docs page, in Bangla and English (Constitution: every user-facing string in both).
 * Admins can replace any section's text at /docs/admin; numbers that change come from the API, not from here.
 * Facts are sourced (PMIDs in the text) or measured (evals/RESULTS.md); simulated results are labelled as such.
 */

export type DocLang = "en" | "bn";
export type Part = "pitch" | "tech";
type T = { en: string; bn: string };

export interface DocSection {
  id: string;
  part: Part;
  title: T;
  lead: T;
  points: { en: string[]; bn: string[] };
}

const s = (id: string, part: Part, title: T, lead: T, en: string[], bn: string[]): DocSection => ({
  id,
  part,
  title,
  lead,
  points: { en, bn },
});

export const SECTIONS: DocSection[] = [
  // ------------------------------------------------------------ pitch deck
  s(
    "problem",
    "pitch",
    { en: "Problem", bn: "সমস্যা" },
    {
      en: "Inflammatory bowel disease (Crohn's disease and ulcerative colitis) is rising fast in South Asia, yet most people in Bangladesh have never heard of it.",
      bn: "প্রদাহজনিত অন্ত্রের রোগ (ক্রোনস ডিজিজ ও আলসারেটিভ কোলাইটিস) দক্ষিণ এশিয়ায় দ্রুত বাড়ছে, অথচ বাংলাদেশের বেশির ভাগ মানুষ এর নামই শোনেননি।",
    },
    [
      "6.8 million people lived with IBD worldwide in 2017 (GBD 2017, PMID 31648971).",
      "IBD is rising at an alarming rate in South Asia, and data from the region is scarce (Shenoy et al. 2025, PMID 39954693).",
      "Across 38 centres in our region, one in five Crohn's patients was given TB treatment, and diagnosis took a median of 12 months (Banerjee et al. 2022, PMID 35178742).",
      "There is no cure and no known cause, and food triggers differ from person to person, so no general diet can tell a patient what their own gut can take.",
    ],
    [
      "২০১৭ সালে বিশ্বে ৬৮ লাখ মানুষ আইবিডি নিয়ে বেঁচে ছিলেন (GBD 2017, PMID 31648971)।",
      "দক্ষিণ এশিয়ায় আইবিডি উদ্বেগজনক হারে বাড়ছে, আর এই অঞ্চলের তথ্য খুবই কম (Shenoy ও অন্যান্য ২০২৫, PMID 39954693)।",
      "আমাদের অঞ্চলের ৩৮টি কেন্দ্রে প্রতি পাঁচজন ক্রোনস রোগীর একজনকে যক্ষ্মার চিকিৎসা দেওয়া হয়েছিল, আর রোগ নির্ণয়ে মাঝামাঝি ১২ মাস লেগেছিল (Banerjee ও অন্যান্য ২০২২, PMID 35178742)।",
      "এর কোনো নিরাময় নেই, কারণও জানা নেই, আর কোন খাবারে সমস্যা হয় তা একেকজনের একেক রকম; তাই কোনো সাধারণ ডায়েট বলে দিতে পারে না একজন রোগীর পেট কী সহ্য করবে।",
    ],
  ),
  s(
    "solution",
    "pitch",
    { en: "Solution", bn: "সমাধান" },
    {
      en: "HappyGut is a Bangla-first companion for people with Crohn's disease and ulcerative colitis that learns each patient's own triggers.",
      bn: "HappyGut ক্রোনস ডিজিজ ও আলসারেটিভ কোলাইটিসের রোগীদের জন্য বাংলায় তৈরি একটি সহায়ক, যা প্রত্যেক রোগীর নিজের সমস্যার খাবার ও অভ্যাস চিনতে শেখে।",
    },
    [
      "Snap or type a meal in Bangla or English and get a verdict for each dish: likely OK, caution, likely trigger or not sure, with the reason, the published evidence and a gentler option.",
      "A two-minute nightly diary records foods, reactions, stools, sleep, stress and doses.",
      "The Flare Pattern Finder shows which foods and habits are linked to this person's worse days, always with counts and never as a proven cause.",
      "Remission and flare periods are tracked separately, an early outlook warns before risky days, and a one-page report goes to the doctor.",
      "Warning signs such as heavy bleeding stop all food advice and point to a doctor.",
    ],
    [
      "বাংলা বা ইংরেজিতে খাবারের ছবি তুলুন বা নাম লিখুন, প্রতিটি খাবারের মতামত পাবেন: সম্ভবত ঠিক আছে, সাবধান, সম্ভবত সমস্যা করবে বা নিশ্চিত নই; সঙ্গে কারণ, প্রকাশিত প্রমাণ আর হালকা একটি বিকল্প।",
      "রাতে দুই মিনিটের ডায়েরিতে খাবার, খাবারে কী হয়েছে, পায়খানা, ঘুম, মানসিক চাপ আর ওষুধ লেখা হয়।",
      "প্যাটার্ন ফাইন্ডার দেখায় কোন খাবার ও অভ্যাস এই মানুষটির খারাপ দিনগুলোর সঙ্গে জড়িত, সবসময় সংখ্যা দিয়ে, কখনো প্রমাণিত কারণ হিসেবে নয়।",
      "রেমিশন ও ফ্লেয়ারের সময় আলাদা করে দেখা যায়, ঝুঁকির দিনের আগে আগাম সতর্কতা আসে, আর চিকিৎসকের জন্য এক পাতার রিপোর্ট তৈরি হয়।",
      "বেশি রক্তপাতের মতো বিপদ সংকেত থাকলে খাবারের সব পরামর্শ থেমে যায় এবং ডাক্তারের কাছে যেতে বলা হয়।",
    ],
  ),
  s(
    "why_now",
    "pitch",
    { en: "Why now", bn: "কেন এখন" },
    { en: "Three things changed at once.", bn: "একসঙ্গে তিনটি জিনিস বদলেছে।" },
    [
      "Free-tier multimodal AI can now read a photo of a Bangladeshi plate and Bangla text at no cost per check.",
      "IBD is rising in newly industrialised countries, including ours (Ng et al. 2017, PMID 29050646), while regional data stays scarce.",
      "Keeping the decision in a tested, deterministic engine makes AI safe enough for everyday health self-management: the model reads and explains, it never decides.",
    ],
    [
      "বিনামূল্যের মাল্টিমোডাল এআই এখন কোনো খরচ ছাড়াই বাংলাদেশি খাবারের প্লেটের ছবি আর বাংলা লেখা পড়তে পারে।",
      "নতুন শিল্পোন্নত দেশগুলোতে, আমাদের দেশসহ, আইবিডি বাড়ছে (Ng ও অন্যান্য ২০১৭, PMID 29050646), অথচ এই অঞ্চলের তথ্য এখনো কম।",
      "সিদ্ধান্তটা একটি পরীক্ষিত, নির্দিষ্ট নিয়মের ইঞ্জিনে রাখলে প্রতিদিনের স্বাস্থ্য-যত্নে এআই ব্যবহার নিরাপদ হয়: মডেল পড়ে ও ব্যাখ্যা করে, কখনো সিদ্ধান্ত নেয় না।",
    ],
  ),
  s(
    "demo",
    "pitch",
    { en: "Product demo", bn: "প্রোডাক্ট ডেমো" },
    {
      en: "The app is live. Sign in with a test account (each holds sample records, not real patients) and follow the path below.",
      bn: "অ্যাপটি চালু আছে। একটি পরীক্ষামূলক অ্যাকাউন্ট দিয়ে ঢুকুন (প্রতিটিতে নমুনা তথ্য আছে, আসল রোগীর নয়) এবং নিচের ধাপগুলো দেখুন।",
    },
    [
      "Check a meal: type \"kacchi biryani, borhani, firni\" or take a photo.",
      "Open \"Why? See the evidence\" on a dish, then add the meal to the diary.",
      "Fill in tonight's diary, then open My patterns, My Gut and the doctor's report.",
      "Turn on \"stricture\" in Settings → Health profile and check the same meal again to see the verdicts change.",
    ],
    [
      "খাবার যাচাই করুন: \"কাচ্চি বিরিয়ানি, বোরহানি, ফিরনি\" লিখুন বা ছবি তুলুন।",
      "কোনো খাবারে \"কেন? প্রমাণ দেখুন\" খুলুন, তারপর খাবারটি ডায়েরিতে যোগ করুন।",
      "আজ রাতের ডায়েরি পূরণ করুন, তারপর আমার প্যাটার্ন, আমার পেট আর চিকিৎসকের রিপোর্ট দেখুন।",
      "সেটিংস → স্বাস্থ্য প্রোফাইলে \"স্ট্রিকচার\" চালু করে একই খাবার আবার যাচাই করুন, মতামত কীভাবে বদলায় দেখবেন।",
    ],
  ),
  s(
    "market",
    "pitch",
    { en: "Market opportunity", bn: "বাজারের সুযোগ" },
    {
      en: "We start where the need is least served and the data is most missing: Bangladesh.",
      bn: "আমরা শুরু করছি যেখানে প্রয়োজন সবচেয়ে কম মেটানো হয় আর তথ্য সবচেয়ে কম: বাংলাদেশে।",
    },
    [
      "Beachhead: people with IBD in Bangladesh and the Bangla-speaking diaspora, plus the caregivers who cook for them and their gastroenterologists.",
      "Next: South Asia, where IBD is rising fastest; then the 6.8 million people with IBD worldwide.",
      "Expansion is mostly data, not code: a new cuisine or language is a new set of dish and text files.",
      "There is no reliable count yet of people with IBD in Bangladesh; studies here are few (Ghosh et al. 2023, PMID 37283595), which is part of the problem we address.",
    ],
    [
      "শুরুর বাজার: বাংলাদেশের আইবিডি রোগী ও প্রবাসী বাংলাভাষী রোগী, তাঁদের জন্য যাঁরা রান্না করেন এবং তাঁদের গ্যাস্ট্রোএন্টারোলজিস্ট।",
      "এরপর: দক্ষিণ এশিয়া, যেখানে আইবিডি সবচেয়ে দ্রুত বাড়ছে; তারপর বিশ্বের ৬৮ লাখ আইবিডি রোগী।",
      "বিস্তার মূলত তথ্যের কাজ, কোডের নয়: নতুন রান্না বা ভাষা মানে খাবার ও লেখার নতুন কিছু ফাইল।",
      "বাংলাদেশে আইবিডি রোগী কতজন, তার নির্ভরযোগ্য হিসাব এখনো নেই; এখানে গবেষণা খুব কম (Ghosh ও অন্যান্য ২০২৩, PMID 37283595), আর এটাই আমাদের সমস্যার একটি অংশ।",
    ],
  ),
  s(
    "business_model",
    "pitch",
    { en: "Business model", bn: "ব্যবসার মডেল" },
    { en: "Planned revenue streams, clinic licence first:", bn: "পরিকল্পিত আয়ের পথ, প্রথমে ক্লিনিক লাইসেন্স:" },
    [
      "Clinic licence (primary): hospitals and GI clinics get pre-visit reports and remote follow-up for their IBD patients.",
      "Freemium for patients: free checks with limits; premium for unlimited checks, insights and meal ideas, priced for Bangladesh.",
      "Patient-support programmes: advice-free medicine and test reminders, a well-established paid category.",
      "Research insights: consented, anonymised, aggregate statistics only, once real patients choose to share.",
    ],
    [
      "ক্লিনিক লাইসেন্স (প্রধান): হাসপাতাল ও জিআই ক্লিনিক তাদের আইবিডি রোগীদের জন্য সাক্ষাতের আগের রিপোর্ট ও দূর থেকে খোঁজ রাখার সুবিধা পায়।",
      "রোগীদের জন্য ফ্রিমিয়াম: সীমিত যাচাই বিনামূল্যে; সীমাহীন যাচাই, বিশ্লেষণ ও খাবারের আইডিয়ার জন্য প্রিমিয়াম, বাংলাদেশের উপযোগী দামে।",
      "রোগী-সহায়তা কর্মসূচি: পরামর্শ ছাড়া শুধু ওষুধ ও পরীক্ষার রিমাইন্ডার, যা একটি প্রতিষ্ঠিত অর্থ-প্রদেয় ক্ষেত্র।",
      "গবেষণার তথ্য: শুধু সম্মতি নিয়ে, নাম-পরিচয় বাদ দিয়ে, সামষ্টিক পরিসংখ্যান; আসল রোগীরা শেয়ার করতে চাইলে তবেই।",
    ],
  ),
  s(
    "traction",
    "pitch",
    { en: "Traction", bn: "অগ্রগতি" },
    {
      en: "A working prototype with measured results. No real patients yet: the results below come from simulated patients and team-written test sets.",
      bn: "মাপা ফলাফলসহ একটি চালু প্রোটোটাইপ। এখনো কোনো আসল রোগী নেই: নিচের ফলাফল কৃত্রিম রোগী ও দলের লেখা পরীক্ষার সেট থেকে।",
    },
    [
      "Built step by step since 22 October; every pull request passes automated tests before it merges.",
      "The live counts below are what the running server holds right now (sample accounts plus anything judges add).",
    ],
    [
      "২২ অক্টোবর থেকে ধাপে ধাপে তৈরি; প্রতিটি পুল রিকোয়েস্ট স্বয়ংক্রিয় পরীক্ষা পার হয়ে তবেই যুক্ত হয়।",
      "নিচের লাইভ সংখ্যাগুলো এই মুহূর্তে চালু সার্ভারে যা আছে তা (নমুনা অ্যাকাউন্ট আর বিচারকেরা যা যোগ করেছেন)।",
    ],
  ),
  s(
    "competition",
    "pitch",
    { en: "Competition", bn: "প্রতিযোগিতা" },
    { en: "What patients use today, and what is missing:", bn: "রোগীরা আজ কী ব্যবহার করেন, আর কী নেই:" },
    [
      "Symptom trackers record what happened, but don't judge a meal before it's eaten.",
      "Generic and low-FODMAP diet apps give one list for everyone and don't know Bangladeshi dishes.",
      "General AI chatbots can answer differently each time, don't learn from a personal diary, and don't stop when a warning sign appears.",
      "Doctors' advice is personal but brief and infrequent; patients decide alone at every meal.",
    ],
    [
      "উপসর্গ লেখার অ্যাপ কী হয়েছে তা লিখে রাখে, কিন্তু খাওয়ার আগে খাবার নিয়ে মতামত দেয় না।",
      "সাধারণ ও লো-ফডম্যাপ ডায়েট অ্যাপ সবার জন্য একই তালিকা দেয় এবং বাংলাদেশি খাবার চেনে না।",
      "সাধারণ এআই চ্যাটবট একেকবার একেক উত্তর দিতে পারে, ব্যক্তিগত ডায়েরি থেকে শেখে না, আর বিপদ সংকেত দেখলেও থামে না।",
      "ডাক্তারের পরামর্শ ব্যক্তিগত, কিন্তু সংক্ষিপ্ত ও মাঝে মাঝে; প্রতিটি খাবারে রোগীকে একাই সিদ্ধান্ত নিতে হয়।",
    ],
  ),
  s(
    "advantage",
    "pitch",
    { en: "Unique advantage", bn: "আমাদের বিশেষত্ব" },
    { en: "Why this is hard to copy:", bn: "কেন এটি নকল করা কঠিন:" },
    [
      "A food knowledge graph of 109 dishes eaten in Bangladesh, with Bangla, English and English-letter names, linked to 25 Rule Cards that quote published IBD research.",
      "A deterministic, unit-tested verdict engine: the same meal always gets the same answer, and every warning cites its rule.",
      "Personal N-of-1 learning: each patient's own diary decides what is linked to their worse days.",
      "Safety and privacy built in: red flags first, personal details removed before any cloud AI call, photos never stored.",
      "Runs at $0 on free tiers, which matters for patients and clinics in Bangladesh.",
    ],
    [
      "বাংলাদেশে খাওয়া ১০৯টি খাবারের জ্ঞানভান্ডার, বাংলা, ইংরেজি ও ইংরেজি অক্ষরে নামসহ, যা প্রকাশিত আইবিডি গবেষণার বাক্য উদ্ধৃত করা ২৫টি নিয়ম-কার্ডের সঙ্গে যুক্ত।",
      "নির্দিষ্ট নিয়মের, পরীক্ষিত মতামত-ইঞ্জিন: একই খাবারে সবসময় একই উত্তর, আর প্রতিটি সতর্কতার পেছনে একটি নিয়মের সূত্র।",
      "ব্যক্তিগত শেখা: প্রত্যেক রোগীর নিজের ডায়েরিই ঠিক করে কোন জিনিস তাঁর খারাপ দিনের সঙ্গে জড়িত।",
      "নিরাপত্তা ও গোপনীয়তা শুরু থেকেই: আগে বিপদ সংকেত দেখা, যেকোনো ক্লাউড এআই-এর আগে ব্যক্তিগত তথ্য মুছে ফেলা, ছবি কখনো রাখা হয় না।",
      "বিনামূল্যের সেবায় শূন্য খরচে চলে, যা বাংলাদেশের রোগী ও ক্লিনিকের জন্য জরুরি।",
    ],
  ),
  s(
    "go_to_market",
    "pitch",
    { en: "Go-to-market", bn: "বাজারে পৌঁছানোর পরিকল্পনা" },
    { en: "Clinic first, then patients directly:", bn: "প্রথমে ক্লিনিক, তারপর সরাসরি রোগী:" },
    [
      "Pilot with gastroenterology clinics in Dhaka: doctors invite their IBD patients and receive the pre-visit report.",
      "Pilot measures: 4-week diary retention, symptom-free days and food-related quality of life (FR-QoL-29).",
      "Grow through patient communities and Bangla awareness content about Crohn's and colitis.",
      "Then the Bangla-speaking diaspora and the wider South Asian region.",
    ],
    [
      "ঢাকার গ্যাস্ট্রোএন্টারোলজি ক্লিনিকের সঙ্গে পাইলট: ডাক্তাররা তাঁদের আইবিডি রোগীদের আমন্ত্রণ জানাবেন এবং সাক্ষাতের আগের রিপোর্ট পাবেন।",
      "পাইলটে যা মাপা হবে: ৪ সপ্তাহ ডায়েরি চালিয়ে যাওয়া, উপসর্গহীন দিন এবং খাবার-সম্পর্কিত জীবনের মান (FR-QoL-29)।",
      "রোগীদের কমিউনিটি এবং ক্রোনস ও কোলাইটিস নিয়ে বাংলায় সচেতনতামূলক লেখার মাধ্যমে বাড়ানো।",
      "এরপর প্রবাসী বাংলাভাষী এবং দক্ষিণ এশিয়ার বৃহত্তর অঞ্চল।",
    ],
  ),
  s(
    "team",
    "pitch",
    { en: "Team", bn: "দল" },
    { en: "The people building HappyGut.", bn: "যাঁরা HappyGut তৈরি করছেন।" },
    [],
    [],
  ),
  s(
    "vision",
    "pitch",
    { en: "Vision", bn: "আমাদের লক্ষ্য" },
    {
      en: "From Bangladesh to the world: help every person with IBD know their own gut, and help research finally see South Asian patients.",
      bn: "বাংলাদেশ থেকে বিশ্বে: আইবিডিতে আক্রান্ত প্রত্যেক মানুষ যেন নিজের পেটকে জানতে পারেন, আর গবেষণা যেন অবশেষে দক্ষিণ এশিয়ার রোগীদের দেখতে পায়।",
    },
    [
      "If thousands of patients choose to share anonymised patterns, machine learning could show researchers what no single clinic can see.",
      "Awareness: more people in Bangladesh should know what Crohn's disease and colitis are, so diagnosis comes sooner.",
      "Bangladesh could help answer a global question about why IBD happens and what triggers it.",
    ],
    [
      "হাজারো রোগী যদি নাম-পরিচয় ছাড়া তাঁদের প্যাটার্ন শেয়ার করতে চান, মেশিন লার্নিং গবেষকদের এমন কিছু দেখাতে পারে যা কোনো একক ক্লিনিক দেখতে পায় না।",
      "সচেতনতা: বাংলাদেশে আরও মানুষ জানুক ক্রোনস ডিজিজ ও কোলাইটিস কী, যাতে রোগ তাড়াতাড়ি ধরা পড়ে।",
      "আইবিডি কেন হয় আর কিসে বাড়ে, এই বৈশ্বিক প্রশ্নের উত্তরে বাংলাদেশ অবদান রাখতে পারে।",
    ],
  ),

  // ------------------------------------------------------------ technical documentation
  s(
    "overview",
    "tech",
    { en: "Product overview", bn: "প্রোডাক্টের পরিচিতি" },
    {
      en: "What HappyGut does, for whom, and the core use cases.",
      bn: "HappyGut কী করে, কাদের জন্য, আর প্রধান ব্যবহারগুলো।",
    },
    [
      "Users: adults with Crohn's disease or ulcerative colitis (Bangla-first, mobile); the caregivers who cook; their gastroenterologists, through the report.",
      "Use case 1: before eating, check a meal and get a personal, cited verdict per dish.",
      "Use case 2: each night, a two-minute diary; over weeks, see what is linked to worse days.",
      "Use case 3: track remission and flare periods, weight, medicines and tests; take a one-page report to the doctor.",
      "Not a medical device: it never diagnoses, never says a food is \"safe\" and never gives medicine advice.",
    ],
    [
      "ব্যবহারকারী: ক্রোনস ডিজিজ বা আলসারেটিভ কোলাইটিসে আক্রান্ত প্রাপ্তবয়স্ক (প্রথমে বাংলা, মোবাইলে); যাঁরা রান্না করেন; আর রিপোর্টের মাধ্যমে তাঁদের গ্যাস্ট্রোএন্টারোলজিস্ট।",
      "ব্যবহার ১: খাওয়ার আগে খাবার যাচাই করে প্রতিটি খাবারের ব্যক্তিগত, সূত্রসহ মতামত।",
      "ব্যবহার ২: প্রতি রাতে দুই মিনিটের ডায়েরি; কয়েক সপ্তাহে দেখা যায় কোন জিনিস খারাপ দিনের সঙ্গে জড়িত।",
      "ব্যবহার ৩: রেমিশন ও ফ্লেয়ারের সময়, ওজন, ওষুধ ও পরীক্ষার হিসাব; ডাক্তারের কাছে এক পাতার রিপোর্ট।",
      "এটি চিকিৎসা যন্ত্র নয়: রোগ নির্ণয় করে না, কোনো খাবারকে \"নিরাপদ\" বলে না এবং ওষুধ নিয়ে পরামর্শ দেয় না।",
    ],
  ),
  s(
    "features",
    "tech",
    { en: "Feature matrix", bn: "ফিচারের তালিকা" },
    {
      en: "Status read from the running server: \"live\" means it works right now on this deployment.",
      bn: "অবস্থা চালু সার্ভার থেকে পড়া: \"চালু\" মানে এই মুহূর্তে এই সার্ভারে কাজ করছে।",
    },
    [],
    [],
  ),
  s(
    "architecture",
    "tech",
    { en: "Architecture", bn: "কাঠামো" },
    {
      en: "UI → API → services → data. The decision stays in the deterministic engine; models only read and explain.",
      bn: "ইন্টারফেস → এপিআই → সার্ভিস → তথ্য। সিদ্ধান্ত থাকে নির্দিষ্ট নিয়মের ইঞ্জিনে; মডেল শুধু পড়ে আর ব্যাখ্যা করে।",
    },
    [
      "Web app: React PWA on Vercel, Bangla and English, installable on a phone.",
      "API: FastAPI on Render; the meal check is a LangGraph flow streamed to the phone over Server-Sent Events.",
      "Knowledge: 109 dishes and 25 Rule Cards as reviewed YAML files, loaded into an in-memory graph.",
      "Storage: the prototype keeps the sample accounts in memory; Supabase Postgres migrations (row-level security, consent, audit) are written and tested for real users.",
      "Around it: n8n for scheduled jobs, Langfuse for traces, and four read-only MCP servers for AI clients.",
    ],
    [
      "ওয়েব অ্যাপ: Vercel-এ React PWA, বাংলা ও ইংরেজি, ফোনে ইনস্টল করা যায়।",
      "এপিআই: Render-এ FastAPI; খাবার যাচাই একটি LangGraph ধারা, যা Server-Sent Events দিয়ে ফোনে ধাপে ধাপে আসে।",
      "জ্ঞানভান্ডার: যাচাই করা YAML ফাইলে ১০৯টি খাবার ও ২৫টি নিয়ম-কার্ড, মেমরিতে একটি গ্রাফে লোড হয়।",
      "সংরক্ষণ: প্রোটোটাইপ নমুনা অ্যাকাউন্টগুলো মেমরিতে রাখে; আসল ব্যবহারকারীদের জন্য Supabase Postgres-এর মাইগ্রেশন (রো-লেভেল সিকিউরিটি, সম্মতি, অডিট) লেখা ও পরীক্ষা করা আছে।",
      "চারপাশে: নির্ধারিত কাজের জন্য n8n, ট্রেসের জন্য Langfuse, আর এআই ক্লায়েন্টদের জন্য চারটি শুধু-পড়ার MCP সার্ভার।",
    ],
  ),
  s(
    "data_flow",
    "tech",
    { en: "Data flow", bn: "তথ্যের প্রবাহ" },
    {
      en: "Input → processing → AI → output → feedback, for one meal check and the diary loop.",
      bn: "ইনপুট → প্রক্রিয়া → এআই → ফলাফল → ফিডব্যাক, একটি খাবার যাচাই ও ডায়েরির চক্রে।",
    },
    [],
    [],
  ),
  s(
    "stack",
    "tech",
    { en: "Technology stack", bn: "প্রযুক্তি" },
    { en: "Open source wherever possible; free tiers with no card.", bn: "যেখানে সম্ভব ওপেন সোর্স; কার্ড ছাড়া বিনামূল্যের সেবা।" },
    [
      "Frontend: React 19, Vite, Tailwind CSS, TanStack Query, Zod, react-i18next, Recharts, installable PWA.",
      "Backend: Python 3.11, FastAPI, Pydantic v2, LangGraph, Pydantic-AI, Server-Sent Events.",
      "AI: Gemini (Google AI Studio free tier), Groq (gpt-oss-120b fallback), LightGBM with SHAP, Microsoft Presidio + spaCy.",
      "Data: YAML knowledge seeds, in-memory graph; Supabase Postgres with pg_trgm and pg_cron prepared; offline Ollama jobs (Gemma 3 12B) and BGE-M3 embeddings.",
      "Infra and tools: Vercel, Render, n8n, Langfuse, MCP Python SDK, GitHub Actions, Playwright, Claude Code.",
    ],
    [
      "ফ্রন্টএন্ড: React 19, Vite, Tailwind CSS, TanStack Query, Zod, react-i18next, Recharts, ইনস্টলযোগ্য PWA।",
      "ব্যাকএন্ড: Python 3.11, FastAPI, Pydantic v2, LangGraph, Pydantic-AI, Server-Sent Events।",
      "এআই: Gemini (Google AI Studio-র বিনামূল্যের স্তর), Groq (বিকল্প gpt-oss-120b), SHAP-সহ LightGBM, Microsoft Presidio + spaCy।",
      "তথ্য: YAML জ্ঞানভান্ডার, মেমরিতে গ্রাফ; pg_trgm ও pg_cron-সহ Supabase Postgres প্রস্তুত; অফলাইন Ollama কাজ (Gemma 3 12B) ও BGE-M3 এমবেডিং।",
      "ইনফ্রা ও টুল: Vercel, Render, n8n, Langfuse, MCP Python SDK, GitHub Actions, Playwright, Claude Code।",
    ],
  ),
  s(
    "api",
    "tech",
    { en: "API documentation", bn: "এপিআই ডকুমেন্টেশন" },
    {
      en: "Every endpoint below is read from the running API's own route table, so this list cannot drift from the code.",
      bn: "নিচের প্রতিটি এন্ডপয়েন্ট চালু এপিআই-এর নিজের রুট-তালিকা থেকে পড়া, তাই এই তালিকা কোডের সঙ্গে অমিল হতে পারে না।",
    },
    [
      "Patient endpoints need a sign-in token (signed, 12-hour expiry; repeated wrong passwords lock an email for 5 minutes).",
      "Job endpoints need the n8n bearer token; docs-admin endpoints need the admin token from /docs/admin.",
      "APIs we call: Gemini and Groq (models), Langfuse (traces, optional); Europe PMC was used offline to confirm every quoted source.",
    ],
    [
      "রোগীর এন্ডপয়েন্টে সাইন-ইন টোকেন লাগে (স্বাক্ষরিত, ১২ ঘণ্টা মেয়াদ; বারবার ভুল পাসওয়ার্ডে ইমেইলটি ৫ মিনিট বন্ধ থাকে)।",
      "নির্ধারিত কাজের এন্ডপয়েন্টে n8n-এর টোকেন লাগে; ডকস-অ্যাডমিন এন্ডপয়েন্টে /docs/admin থেকে পাওয়া টোকেন লাগে।",
      "আমরা যেসব এপিআই ডাকি: Gemini ও Groq (মডেল), Langfuse (ট্রেস, ঐচ্ছিক); প্রতিটি উদ্ধৃত সূত্র যাচাইয়ে অফলাইনে Europe PMC ব্যবহার করা হয়েছে।",
    ],
  ),
  s(
    "data_layer",
    "tech",
    { en: "Data layer", bn: "তথ্যের স্তর" },
    { en: "Where data comes from, where it lives and how it is protected.", bn: "তথ্য কোথা থেকে আসে, কোথায় থাকে আর কীভাবে সুরক্ষিত থাকে।" },
    [
      "Sources: dishes written by the team; Rule Cards drafted from open-access IBD guidance, each paper confirmed by DOI / PMID and its exact sentence retrieved; every item reviewed by an LLM judge (not clinical review).",
      "No scraping: knowledge is authored from licensed sources, with each licence recorded.",
      "Patient data: the prototype holds sample accounts only, labelled as sample data; evaluation uses a labelled simulated cohort.",
      "Privacy: personal details removed before any cloud AI call (Bangladesh rules + Presidio); photos checked, stripped of location data, read once and never stored.",
    ],
    [
      "উৎস: খাবারগুলো দলের লেখা; নিয়ম-কার্ড খোলা আইবিডি নির্দেশিকা থেকে খসড়া, প্রতিটি গবেষণাপত্র DOI / PMID দিয়ে নিশ্চিত ও তার হুবহু বাক্যসহ; প্রতিটি জিনিস একটি এলএলএম বিচারক যাচাই করেছে (চিকিৎসকের যাচাই নয়)।",
      "কোনো স্ক্র্যাপিং নেই: জ্ঞানভান্ডার লাইসেন্সপ্রাপ্ত উৎস থেকে লেখা, প্রতিটি লাইসেন্স লিখে রাখা।",
      "রোগীর তথ্য: প্রোটোটাইপে শুধু নমুনা অ্যাকাউন্ট, নমুনা হিসেবে চিহ্নিত; মূল্যায়নে চিহ্নিত কৃত্রিম রোগীর দল ব্যবহার করা হয়।",
      "গোপনীয়তা: যেকোনো ক্লাউড এআই-এর আগে ব্যক্তিগত তথ্য মুছে ফেলা হয় (বাংলাদেশি নিয়ম + Presidio); ছবি যাচাই করে অবস্থানের তথ্য সরিয়ে একবার পড়া হয়, কখনো রাখা হয় না।",
    ],
  ),
  s(
    "ai_layer",
    "tech",
    { en: "AI layer", bn: "এআই স্তর" },
    { en: "Which models do what, and how results stay explainable.", bn: "কোন মডেল কী করে, আর ফলাফল কীভাবে ব্যাখ্যাযোগ্য থাকে।" },
    [
      "Perception: Gemini reads a photo or text into dishes as JSON; typed dish names are matched locally without a model call.",
      "Graph retrieval: dish → ingredients → components → Rule Cards for this patient's diagnosis and state → the paper and its quoted sentence.",
      "Decision: a deterministic engine; stricture rules first; no evidence means \"not sure\".",
      "Explanation: Gemini (Groq as fallback) explains only the engine's verdict and the retrieved evidence; a guard checks the text and falls back to a template.",
      "Personalisation: the Bayesian Pattern Finder (≥ 3 exposures, \"linked to\", never \"caused\") and a LightGBM flare estimate with SHAP drivers, trained on simulated patients.",
    ],
    [
      "পড়া: Gemini ছবি বা লেখা থেকে খাবারগুলো JSON আকারে বের করে; লেখা খাবারের নাম মডেল ছাড়াই মেলানো হয়।",
      "গ্রাফ থেকে খোঁজা: খাবার → উপকরণ → উপাদান → রোগীর রোগ ও অবস্থার নিয়ম-কার্ড → গবেষণাপত্র ও তার উদ্ধৃত বাক্য।",
      "সিদ্ধান্ত: নির্দিষ্ট নিয়মের ইঞ্জিন; আগে স্ট্রিকচারের নিয়ম; প্রমাণ না থাকলে \"নিশ্চিত নই\"।",
      "ব্যাখ্যা: Gemini (বিকল্প Groq) শুধু ইঞ্জিনের মতামত আর পাওয়া প্রমাণ ব্যাখ্যা করে; একটি যাচাই-ধাপ লেখাটি মিলিয়ে দেখে, না মিললে নির্দিষ্ট ছকের লেখা দেখায়।",
      "ব্যক্তিগতকরণ: বেইজিয়ান প্যাটার্ন ফাইন্ডার (অন্তত ৩ বার, \"জড়িত\", কখনো \"কারণ\" নয়) আর SHAP কারণসহ LightGBM ফ্লেয়ার অনুমান, কৃত্রিম রোগীর তথ্যে শেখানো।",
    ],
  ),
  s(
    "roadmap",
    "tech",
    { en: "Product roadmap", bn: "পরবর্তী পরিকল্পনা" },
    { en: "What comes next, in order.", bn: "এরপর কী আসবে, ক্রম অনুযায়ী।" },
    [
      "Short term (before the finals, 26 December): real sign-up with Supabase Auth and Postgres storage; load the knowledge into Neo4j and pgvector; measure photo recognition on a licensed photo set.",
      "Mid term: a Dhaka clinic pilot; a dietitian-labelled verdict set; consented diaries from real users; retrain the flare model on real data.",
      "Long term: more cuisines and languages; research outputs as anonymised aggregates only; Bangla voice input once audio can stay private.",
    ],
    [
      "স্বল্পমেয়াদি (ফাইনালের আগে, ২৬ ডিসেম্বর): Supabase Auth ও Postgres দিয়ে আসল সাইন-আপ; জ্ঞানভান্ডার Neo4j ও pgvector-এ তোলা; লাইসেন্সপ্রাপ্ত ছবির সেটে ছবি চেনার নির্ভুলতা মাপা।",
      "মধ্যমেয়াদি: ঢাকার ক্লিনিকে পাইলট; পুষ্টিবিদের চিহ্নিত মতামতের সেট; আসল ব্যবহারকারীর সম্মতিসহ ডায়েরি; আসল তথ্যে ফ্লেয়ার মডেল নতুন করে শেখানো।",
      "দীর্ঘমেয়াদি: আরও রান্না ও ভাষা; গবেষণার জন্য শুধু নাম-পরিচয়হীন সামষ্টিক ফলাফল; অডিও গোপন রাখা গেলে বাংলায় ভয়েস ইনপুট।",
    ],
  ),
  s(
    "performance",
    "tech",
    { en: "Performance & scalability", bn: "গতি ও বিস্তারযোগ্যতা" },
    { en: "Measured where we could, planned where we couldn't yet.", bn: "যেখানে পেরেছি মেপেছি, বাকিটা পরিকল্পিত।" },
    [
      "The verdict engine rates a three-dish meal in about 0.16 ms (median, 300 runs); the decision itself never waits for a model.",
      "At most two model calls per meal check; typed dish names need none; the small model is tried first.",
      "The backend peaks at about 260 MB of memory, inside a free 512 MB server; the LightGBM model runs in-process.",
      "Scaling: the API is stateless apart from storage, so moving storage to Postgres lets it run on several servers; knowledge loads once at start-up.",
      "Not measured yet: full check time on a phone connection, including the photo and the explanation.",
    ],
    [
      "মতামত-ইঞ্জিন তিনটি খাবারের একটি প্লেট প্রায় ০.১৬ মিলিসেকেন্ডে বিচার করে (মাঝামাঝি মান, ৩০০ বার); সিদ্ধান্তের জন্য কখনো মডেলের অপেক্ষা করতে হয় না।",
      "একটি খাবার যাচাইয়ে সর্বোচ্চ দুটি মডেল কল; লেখা নামের জন্য কোনোটাই লাগে না; আগে ছোট মডেল চেষ্টা করা হয়।",
      "ব্যাকএন্ড সর্বোচ্চ প্রায় ২৬০ এমবি মেমরি ব্যবহার করে, যা বিনামূল্যের ৫১২ এমবি সার্ভারে আঁটে; LightGBM মডেল একই প্রক্রিয়ায় চলে।",
      "বিস্তার: সংরক্ষণ ছাড়া এপিআই নিজে কিছু ধরে রাখে না, তাই সংরক্ষণ Postgres-এ নিলে একাধিক সার্ভারে চালানো যায়; জ্ঞানভান্ডার শুরুতে একবার লোড হয়।",
      "এখনো মাপা হয়নি: ফোনের সংযোগে ছবি ও ব্যাখ্যাসহ পুরো যাচাইয়ের সময়।",
    ],
  ),
  s(
    "security",
    "tech",
    { en: "Security", bn: "নিরাপত্তা" },
    { en: "Authentication, roles and data protection.", bn: "পরিচয় যাচাই, ভূমিকা আর তথ্যের সুরক্ষা।" },
    [
      "Authentication: signed session tokens (12 hours); docs admin tokens (8 hours); lockout after repeated wrong passwords.",
      "Roles: patient (only their own records), docs admin (this page's settings), job token (n8n), MCP bearer token for the HTTP servers.",
      "Data protection: HTTPS everywhere; personal details removed before cloud AI; photos never stored; no real patient data in the prototype.",
      "Prepared for real users: row-level security on every patient table, revocable consent records and an audit log (Supabase migrations, tested in CI).",
      "Every pull request passes a secret scan; no keys are kept in the repository.",
    ],
    [
      "পরিচয় যাচাই: স্বাক্ষরিত সেশন টোকেন (১২ ঘণ্টা); ডকস অ্যাডমিন টোকেন (৮ ঘণ্টা); বারবার ভুল পাসওয়ার্ডে সাময়িক বন্ধ।",
      "ভূমিকা: রোগী (শুধু নিজের তথ্য), ডকস অ্যাডমিন (এই পাতার সেটিংস), জব টোকেন (n8n), HTTP সার্ভারের জন্য MCP টোকেন।",
      "তথ্যের সুরক্ষা: সবখানে HTTPS; ক্লাউড এআই-এর আগে ব্যক্তিগত তথ্য মুছে ফেলা; ছবি কখনো রাখা হয় না; প্রোটোটাইপে কোনো আসল রোগীর তথ্য নেই।",
      "আসল ব্যবহারকারীর জন্য প্রস্তুত: প্রতিটি রোগী-টেবিলে রো-লেভেল সিকিউরিটি, প্রত্যাহারযোগ্য সম্মতির রেকর্ড ও অডিট লগ (Supabase মাইগ্রেশন, CI-তে পরীক্ষিত)।",
      "প্রতিটি পুল রিকোয়েস্টে গোপন তথ্যের স্ক্যান হয়; কোনো চাবি রিপোজিটরিতে রাখা হয় না।",
    ],
  ),
  s(
    "analytics",
    "tech",
    { en: "Analytics & KPIs", bn: "বিশ্লেষণ ও লক্ষ্যমাত্রা" },
    { en: "What we will measure in the pilot, and what the server counts now.", bn: "পাইলটে আমরা কী মাপব, আর এখন সার্ভার কী গুনছে।" },
    [
      "Outcome KPIs (pilot): 4-week diary retention, symptom-free days, food-related quality of life (FR-QoL-29), self-reported adherence.",
      "AI quality KPIs: verdict agreement with a dietitian-labelled set, dish recognition on Bangladeshi photos, red-flag recall on new test phrases.",
      "Business KPI: share of interviewed gastroenterologists who would use the pre-visit report.",
    ],
    [
      "ফলাফলের লক্ষ্যমাত্রা (পাইলট): ৪ সপ্তাহ ডায়েরি চালিয়ে যাওয়া, উপসর্গহীন দিন, খাবার-সম্পর্কিত জীবনের মান (FR-QoL-29), নিজে জানানো ওষুধ খাওয়ার নিয়মিততা।",
      "এআই-এর মানের লক্ষ্যমাত্রা: পুষ্টিবিদের চিহ্নিত সেটের সঙ্গে মতামতের মিল, বাংলাদেশি খাবারের ছবি চেনা, নতুন পরীক্ষামূলক বাক্যে বিপদ সংকেত ধরা।",
      "ব্যবসার লক্ষ্যমাত্রা: সাক্ষাৎকার নেওয়া গ্যাস্ট্রোএন্টারোলজিস্টদের কতজন সাক্ষাতের আগের রিপোর্ট ব্যবহার করবেন।",
    ],
  ),
  s(
    "changelog",
    "tech",
    { en: "Changelog", bn: "পরিবর্তনের ইতিহাস" },
    { en: "Version 0.1.0, built step by step, one pull request per step.", bn: "সংস্করণ ০.১.০, ধাপে ধাপে তৈরি, প্রতি ধাপে একটি পুল রিকোয়েস্ট।" },
    [],
    [],
  ),
];

export const CHANGELOG: { date: string; text: T }[] = [
  { date: "2026-11-20", text: { en: "Live /docs page with admin-controlled visibility", bn: "অ্যাডমিন-নিয়ন্ত্রিত লাইভ /docs পাতা" } },
  {
    date: "2026-11-19",
    text: {
      en: "109 dishes (48 added); meals reach the diary with \"Add to diary\"; editable food times; evaluation re-run",
      bn: "১০৯টি খাবার (৪৮টি নতুন); \"ডায়েরিতে যোগ করুন\" দিয়ে খাবার ডায়েরিতে যায়; খাবারের সময় বদলানো যায়; মূল্যায়ন আবার চালানো",
    },
  },
  {
    date: "2026-11-18",
    text: {
      en: "Flare-risk model v1 (LightGBM); weight tracking; medicines and tests; three more MCP servers; Langfuse tracing; n8n workflows",
      bn: "ফ্লেয়ারের ঝুঁকির মডেল v1 (LightGBM); ওজনের হিসাব; ওষুধ ও পরীক্ষা; আরও তিনটি MCP সার্ভার; Langfuse ট্রেসিং; n8n ওয়ার্কফ্লো",
    },
  },
  {
    date: "2026-11-17",
    text: { en: "Measured evaluation; interface redesign; \"How it works\" page", bn: "মাপা মূল্যায়ন; নতুন ইন্টারফেস; \"যেভাবে কাজ করে\" পাতা" },
  },
  {
    date: "2026-11-16",
    text: {
      en: "Test accounts for judges; LLM-judge review of all knowledge; food guide and Personal Gut Graph",
      bn: "বিচারকদের জন্য পরীক্ষামূলক অ্যাকাউন্ট; পুরো জ্ঞানভান্ডারের এলএলএম-বিচারক যাচাই; খাবারের গাইড ও ব্যক্তিগত গাট গ্রাফ",
    },
  },
  {
    date: "2026-11-15",
    text: {
      en: "Meal-check backend, nightly diary, Pattern Finder, periods and the web app; automatic model choice",
      bn: "খাবার যাচাইয়ের ব্যাকএন্ড, রাতের ডায়েরি, প্যাটার্ন ফাইন্ডার, রেমিশন-ফ্লেয়ারের সময় ও ওয়েব অ্যাপ; মডেল স্বয়ংক্রিয়ভাবে বাছাই",
    },
  },
  {
    date: "2026-10-23",
    text: {
      en: "Knowledge layer: database schema, food graph and its MCP server, GPU jobs for spellings and embeddings",
      bn: "জ্ঞানভান্ডারের স্তর: ডেটাবেস কাঠামো, খাবারের গ্রাফ ও তার MCP সার্ভার, বানান ও এমবেডিংয়ের জন্য জিপিইউ কাজ",
    },
  },
  {
    date: "2026-10-22",
    text: { en: "Foundation: project rules, verdict engine, first knowledge drafts", bn: "ভিত্তি: প্রকল্পের নিয়ম, মতামত-ইঞ্জিন, জ্ঞানভান্ডারের প্রথম খসড়া" },
  },
];

/** Labels for the live feature matrix (ids come from the API). */
export const FEATURE_LABELS: Record<string, T> = {
  meal_check_text: { en: "Meal check by text (Bangla / English)", bn: "লিখে খাবার যাচাই (বাংলা / ইংরেজি)" },
  meal_check_photo: { en: "Meal check by photo", bn: "ছবি দিয়ে খাবার যাচাই" },
  ai_explanation: { en: "AI-written explanation", bn: "এআই-এর লেখা ব্যাখ্যা" },
  red_flags: { en: "Red-flag escalation", bn: "বিপদ সংকেতে সতর্কতা" },
  stricture_rules: { en: "Stricture safety rules", bn: "স্ট্রিকচারের নিরাপত্তা নিয়ম" },
  nightly_diary: { en: "Nightly diary (HBI / SCCAI)", bn: "রাতের ডায়েরি (HBI / SCCAI)" },
  pattern_finder: { en: "Flare Pattern Finder", bn: "ফ্লেয়ার প্যাটার্ন ফাইন্ডার" },
  periods: { en: "Remission and flare periods", bn: "রেমিশন ও ফ্লেয়ারের সময়" },
  flare_risk_v0: { en: "Flare-risk outlook (rules)", bn: "ফ্লেয়ারের ঝুঁকির পূর্বাভাস (নিয়ম)" },
  flare_risk_v1: { en: "Flare-risk estimate (LightGBM + SHAP)", bn: "ফ্লেয়ারের ঝুঁকির অনুমান (LightGBM + SHAP)" },
  doctor_report: { en: "Doctor's pre-visit report", bn: "চিকিৎসকের জন্য সাক্ষাতের আগের রিপোর্ট" },
  medicines_tests: { en: "Medicines and tests", bn: "ওষুধ ও পরীক্ষা" },
  weight: { en: "Weight tracking (GLIM notice)", bn: "ওজনের হিসাব (GLIM সতর্কতা)" },
  food_guide: { en: "Food guide and meal ideas", bn: "খাবারের গাইড ও খাবারের আইডিয়া" },
  bangla_english: { en: "Bangla and English everywhere", bn: "সবখানে বাংলা ও ইংরেজি" },
  tracing: { en: "Langfuse tracing", bn: "Langfuse ট্রেসিং" },
  scheduled_jobs: { en: "Scheduled jobs (n8n)", bn: "নির্ধারিত কাজ (n8n)" },
  mcp_servers: { en: "Four read-only MCP servers", bn: "চারটি শুধু-পড়ার MCP সার্ভার" },
  real_signup: { en: "Real sign-up and storage (Supabase)", bn: "আসল সাইন-আপ ও সংরক্ষণ (Supabase)" },
  neo4j_pgvector: { en: "Knowledge in Neo4j and pgvector", bn: "Neo4j ও pgvector-এ জ্ঞানভান্ডার" },
  clinic_pilot: { en: "Dhaka clinic pilot", bn: "ঢাকার ক্লিনিকে পাইলট" },
  research_aggregates: { en: "Research aggregates (consented)", bn: "গবেষণার সামষ্টিক তথ্য (সম্মতিসহ)" },
};

export function sectionText(section: DocSection, lang: DocLang): string {
  const points = section.points[lang].map((p) => `- ${p}`).join("\n");
  return points ? `${section.lead[lang]}\n\n${points}` : section.lead[lang];
}
