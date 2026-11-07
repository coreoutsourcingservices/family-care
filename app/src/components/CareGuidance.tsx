import { useEffect, useState, type ReactNode } from "react";
import { BookOpen, ExternalLink, HeartPulse } from "lucide-react";
import { useCustomerLanguage } from "../../../customer/src/localization/CustomerLanguage";
import { careApi } from "../lib/careApi";
import "./care-guidance.css";

type Copy = [string, string];
type Guide = { title: Copy; tips: Copy[]; source: string; sourceName: string };
const nhs = "https://www.nhs.uk";
const guides: Record<string, Guide> = {
  bp: {
    title: ["Blood pressure care", "ब्लड प्रेशर की देखभाल"],
    tips: [
      [
        "Rest quietly before measuring; sit with your arm supported and record both numbers.",
        "मापने से पहले आराम से बैठें, हाथ को सहारा दें और दोनों रीडिंग लिखें।",
      ],
      [
        "Reduce salty foods, stay active and take medicines as prescribed. Share repeated high readings with your clinician.",
        "नमक कम करें, सक्रिय रहें और दवा डॉक्टर के अनुसार लें। बार-बार अधिक रीडिंग आए तो डॉक्टर से बात करें।",
      ],
    ],
    source: nhs + "/conditions/high-blood-pressure/",
    sourceName: "NHS",
  },
  glucose: {
    title: ["Blood sugar care", "ब्लड शुगर की देखभाल"],
    tips: [
      [
        "Save whether a reading was fasting or after a meal; compare it with the target agreed with your clinician.",
        "रीडिंग खाली पेट या खाने के बाद की है, यह लिखें। डॉक्टर द्वारा तय लक्ष्य से तुलना करें।",
      ],
      [
        "Keep regular balanced meals and activity. Do not change diabetes medicines or begin a restrictive diet on your own.",
        "संतुलित भोजन और नियमित गतिविधि रखें। दवा या सख्त डाइट अपने-आप न बदलें।",
      ],
    ],
    source: nhs + "/conditions/type-2-diabetes/treatment/",
    sourceName: "NHS",
  },
  lipids: {
    title: ["Heart-friendly habits", "दिल के लिए अच्छी आदतें"],
    tips: [
      [
        "Choose more fibre-rich foods and replace some saturated fat with unsaturated fats.",
        "रेशेदार भोजन चुनें और सैचुरेटेड फैट की जगह कुछ अनसैचुरेटेड फैट लें।",
      ],
      [
        "Keep active and review your cholesterol results and medicines with your clinician.",
        "सक्रिय रहें और कोलेस्ट्रॉल रिपोर्ट व दवाओं की डॉक्टर से समीक्षा कराएं।",
      ],
    ],
    source: nhs + "/conditions/high-cholesterol/how-to-lower-your-cholesterol/",
    sourceName: "NHS",
  },
  medicine: {
    title: ["Medicine checklist", "दवाओं की जानकारी"],
    tips: [
      [
        "Keep the medicine name, prescribed dose and timing together. Ask your pharmacist if anything is unclear.",
        "दवा का नाम, निर्धारित मात्रा और समय साथ रखें। कुछ स्पष्ट न हो तो फार्मासिस्ट से पूछें।",
      ],
      [
        "Tell your clinician about side effects and other medicines or supplements. Do not change a prescription yourself.",
        "साइड इफेक्ट और अन्य दवाओं या सप्लीमेंट की जानकारी डॉक्टर को दें। प्रिस्क्रिप्शन खुद न बदलें।",
      ],
    ],
    source:
      "https://www.england.nhs.uk/long-read/medication-safety-management/",
    sourceName: "NHS England",
  },
  lifestyle: {
    title: ["Small daily steps", "रोज़ के छोटे कदम"],
    tips: [
      [
        "Build activity into your day and choose balanced meals. Start gradually if you have been inactive.",
        "दिनचर्या में गतिविधि और संतुलित भोजन जोड़ें। पहले सक्रिय नहीं थे तो धीरे शुरू करें।",
      ],
      [
        "Discuss a suitable routine with your clinician if you have a health condition.",
        "कोई स्वास्थ्य समस्या हो तो अपने लिए सही दिनचर्या डॉक्टर से तय करें।",
      ],
    ],
    source: nhs + "/conditions/high-blood-pressure/",
    sourceName: "NHS",
  },
  cycle: {
    title: ["Your cycle, in context", "अपने पीरियड को समझें"],
    tips: [
      [
        "Track start and end dates, flow, pain and changes that affect your day.",
        "शुरू और खत्म होने की तारीख, रक्तस्राव, दर्द और रोज़मर्रा पर असर लिखें।",
      ],
      [
        "Discuss persistent changes, bleeding between periods, or heavy periods affecting daily life with a clinician.",
        "लगातार बदलाव, पीरियड के बीच रक्तस्राव या दैनिक जीवन पर असर डालने वाले अधिक रक्तस्राव पर डॉक्टर से बात करें।",
      ],
    ],
    source: nhs + "/conditions/periods/",
    sourceName: "NHS",
  },
  pcos: {
    title: ["PCOS & hormone care", "PCOS और हार्मोन की देखभाल"],
    tips: [
      [
        "Track cycle changes and symptoms. PCOS needs clinical assessment; a diary alone cannot diagnose it.",
        "पीरियड में बदलाव और लक्षण लिखें। केवल डायरी से PCOS का निदान नहीं होता; डॉक्टर की जांच ज़रूरी है।",
      ],
      [
        "Discuss long-term metabolic health, wellbeing and any fertility concerns with your clinician.",
        "लंबे समय के स्वास्थ्य, मानसिक स्वास्थ्य और प्रजनन संबंधी चिंताओं पर डॉक्टर से बात करें।",
      ],
    ],
    source:
      "https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome",
    sourceName: "WHO",
  },
  pregnancy: {
    title: ["Pregnancy care notes", "गर्भावस्था की देखभाल"],
    tips: [
      [
        "Keep antenatal appointments and save your clinician-confirmed stage in Pregnancy care.",
        "गर्भावस्था की जांच समय पर कराएं और डॉक्टर द्वारा पुष्टि किया गया चरण सेव करें।",
      ],
      [
        "Choose balanced meals and activity suitable for your pregnancy. Your maternity team can adapt the plan.",
        "संतुलित भोजन और गर्भावस्था के अनुसार गतिविधि चुनें। अपनी स्थिति के अनुसार डॉक्टर से सलाह लें।",
      ],
      [
        "Bleeding, severe headache or severe abdominal pain needs prompt maternity advice; heavy bleeding or collapse needs emergency care.",
        "रक्तस्राव, तेज सिरदर्द या पेट में तेज दर्द पर तुरंत चिकित्सा सलाह लें। बहुत अधिक रक्तस्राव या बेहोशी में आपातकालीन सहायता लें।",
      ],
    ],
    source: nhs + "/pregnancy/keeping-well/",
    sourceName: "NHS",
  },
  fertility: {
    title: ["Planning your next step", "अगले कदम की तैयारी"],
    tips: [
      [
        "Keep cycle history, previous test results and questions together for your appointment.",
        "अपॉइंटमेंट के लिए पीरियड की जानकारी, पिछली रिपोर्ट और सवाल साथ रखें।",
      ],
      [
        "Discuss pregnancy planning and existing health conditions with your clinician. Calendar predictions do not confirm ovulation.",
        "गर्भधारण की योजना और मौजूदा स्वास्थ्य समस्याओं पर डॉक्टर से बात करें। कैलेंडर का अनुमान ओव्यूलेशन की पुष्टि नहीं है।",
      ],
    ],
    source: nhs + "/pregnancy/trying-for-a-baby/trying-to-get-pregnant/",
    sourceName: "NHS",
  },
};
const support: Guide = {
  title: ["For your next appointment", "अगली अपॉइंटमेंट की तैयारी"],
  tips: [
    [
      "Keep a dated record of symptoms, medicines and questions. Bring relevant reports to your clinician.",
      "लक्षण, दवाओं और सवालों की तारीख सहित जानकारी रखें। संबंधित रिपोर्ट डॉक्टर को दिखाएं।",
    ],
    [
      "Ask your clinician which follow-ups and checks are appropriate for your age and health history.",
      "अपनी उम्र और स्वास्थ्य इतिहास के अनुसार सही जांच और फॉलो-अप डॉक्टर से पूछें।",
    ],
  ],
  source: "https://www.england.nhs.uk/long-read/medication-safety-management/",
  sourceName: "NHS England",
};
const aliases: Record<string, string> = {
  nutrition: "lifestyle",
  health: "lifestyle",
  symptoms: "cycle",
  screening: "support",
  history: "support",
  records: "support",
  reports: "support",
  reminder: "medicine",
};
type SavedRecord = {
  kind?: string;
  date?: string;
  systolic?: unknown;
  diastolic?: unknown;
};

function CareGuide({
  section,
  module,
  records,
  profileId,
}: {
  section: string;
  module: string;
  records: SavedRecord[];
  profileId: string;
}) {
  const { language } = useCustomerLanguage();
  const hi = language === "hi";
  const text = (copy: Copy) => copy[hi ? 1 : 0];
  const guide = guides[section] ?? guides[aliases[section]] ?? support;
  const latest = records
    .filter((row) => row.kind === "bp")
    .slice()
    .sort((a, b) => (b.date ?? "").localeCompare(a.date ?? ""))[0];
  const urgent =
    section === "bp" &&
    latest &&
    (Number(latest.systolic) >= 180 || Number(latest.diastolic) >= 120);
  if (module === "child" && section === "growth")
    return <CompactGrowthGuide profileId={profileId} />;
  return (
    <aside className="cg-rail" aria-label="Page guidance">
      <section className="cg-card">
        <span className="cg-kicker">
          <BookOpen size={15} />
          {hi ? "छोटी देखभाल गाइड" : "A little guidance"}
        </span>
        <h2>{text(guide.title)}</h2>
        {module === 'women' && section === 'pregnancy' && <PregnancyStageSummary profileId={profileId}/>}
        {section === "bp" &&
          latest &&
          Number(latest.systolic) > 0 &&
          Number(latest.diastolic) > 0 && (
            <p className="cg-reading">
              {hi ? "पिछली सेव रीडिंग" : "Latest saved reading"}
              <strong>
                {String(latest.systolic)}/{String(latest.diastolic)}{" "}
                <small>mmHg</small>
              </strong>
              <small>{latest.date}</small>
            </p>
          )}
        <ul>
          {guide.tips.map((tip, i) => (
            <li key={i}>{text(tip)}</li>
          ))}
        </ul>
        {urgent && (
          <div className="cg-urgent">
            <HeartPulse size={17} />
            <p>
              {hi
                ? "यह सेव की गई रीडिंग बहुत अधिक थी। वर्तमान रीडिंग भी इतनी अधिक हो तो एक मिनट बाद दोबारा मापें और अधिक बनी रहे तो तुरंत डॉक्टर से संपर्क करें। सीने में दर्द, सांस की तकलीफ, कमजोरी या दृष्टि में बदलाव हो तो आपातकालीन सहायता लें।"
                : "This saved reading was very high. If a current reading is also this high, recheck after at least one minute and contact a clinician immediately if it stays high. With chest pain, breathlessness, weakness or vision changes, seek emergency care now."}
            </p>
            <a
              href="https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings"
              target="_blank"
              rel="noreferrer"
            >
              American Heart Association
            </a>
          </div>
        )}
        <p className="cg-note">
          {hi
            ? "सामान्य जानकारी। आपकी देखभाल डॉक्टर आपकी स्थिति के अनुसार तय करेंगे।"
            : "General information; your clinician can adapt it to your health needs."}
        </p>
        <a
          className="cg-source"
          href={guide.source}
          target="_blank"
          rel="noreferrer"
        >
          {guide.sourceName} · {hi ? "संदर्भ" : "Reference"}
          <ExternalLink size={12} />
        </a>
      </section>
    </aside>
  );
}
function PregnancyStageSummary({profileId}:{profileId:string}) {
  const [stage,setStage]=useState<{week:number;month:number;focus:string;needs_stage_review:boolean;food:{text:string}[];daily_care:{text:string}[]}|null>(null);
  const [error,setError]=useState('');
  useEffect(()=>{let active=true;setStage(null);setError('');careApi<{guide:typeof stage}>(`/women/profiles/${profileId}/pregnancy-care`).then(data=>{if(active)setStage(data.guide);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[profileId]);
  if(error)return <p role="status">Saved pregnancy guidance could not be loaded. Your general reference remains available.</p>;
  if(!stage)return <p className="cg-note">Save your pregnancy stage to see week-specific guidance.</p>;
  if(stage.needs_stage_review)return <p className="cg-note">Review your saved pregnancy stage with your maternity clinician.</p>;
  return <div className="cg-stage"><strong>Week {stage.week} · Month {stage.month}</strong><p>{stage.focus}</p>{stage.food?.[0]&&<p>{stage.food[0].text}</p>}{stage.daily_care?.[0]&&<p>{stage.daily_care[0].text}</p>}</div>;
}

type GrowthGuide = {
  active: boolean;
  status: string;
  age_band?: { label: string };
  guide?: {
    notice: string;
    nutrition: { foods?: string; meal_frequency?: string };
    sources: { title: string; url: string }[];
  } | null;
};
function CompactGrowthGuide({ profileId }: { profileId: string }) {
  const [data, setData] = useState<GrowthGuide>(),
    [error, setError] = useState(""),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setData(undefined);
    careApi<GrowthGuide>(`/children/${profileId}/growth-nutrition-guide`)
      .then((value) => {
        if (active) {
          setData(value);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [profileId, attempt]);
  return (
    <aside className="cg-rail" aria-label="Page guidance">
      <section className="cg-card">
        <span className="cg-kicker">
          <BookOpen size={15} />
          Age-based reference
        </span>
        <h2>Growth & nutrition</h2>
        {error ? (
          <>
            <p role="alert">{error}</p>
            <button onClick={() => setAttempt((n) => n + 1)}>
              Retry guide
            </button>
          </>
        ) : !data ? (
          <p role="status">Loading age-based guide...</p>
        ) : !data.active ? (
          <p>Your connected doctor has turned this guide off.</p>
        ) : !data.guide ? (
          <p>Age-based guidance is available for ages 0–12.</p>
        ) : (
          <>
            <strong className="cg-band">{data.age_band?.label}</strong>
            {data.guide.nutrition.foods && <p>{data.guide.nutrition.foods}</p>}
            {data.guide.nutrition.meal_frequency && (
              <p>{data.guide.nutrition.meal_frequency}</p>
            )}
            <p className="cg-note">{data.guide.notice}</p>
            {data.guide.sources.slice(0, 2).map((source) => (
              <a
                className="cg-source"
                key={source.url}
                href={source.url}
                target="_blank"
                rel="noreferrer"
              >
                {source.title}
                <ExternalLink size={12} />
              </a>
            ))}
          </>
        )}
      </section>
    </aside>
  );
}
export default function CareGuidanceLayout({
  module,
  section,
  records = [],
  profileId,
  children,
}: {
  module: string;
  section: string;
  records?: SavedRecord[];
  profileId: string;
  children: ReactNode;
}) {
  const relevant =
    module === "child"
      ? section === "growth"
      : Boolean(guides[section] || aliases[section]);
  if (!relevant) return <>{children}</>;
  return (
    <div className={"cg-layout cg-" + module}>
      <div className="cg-main">{children}</div>
      <CareGuide
        key={profileId + section}
        module={module}
        section={section}
        records={records}
        profileId={profileId}
      />
    </div>
  );
}
