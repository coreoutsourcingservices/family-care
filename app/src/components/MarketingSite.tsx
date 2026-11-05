import {useEffect,useRef,useState,type ReactNode} from 'react';
import {Link,NavLink,useLocation} from 'react-router-dom';
import {ArrowRight,ArrowLeft,Search,Menu,X,ChevronDown,Plus,Heart,ShieldCheck,Users,CalendarDays,FolderHeart,Mail,Stethoscope,Baby,Activity,Leaf,BookOpen} from 'lucide-react';
import '../marketing.css';

export const marketingAssets={home:'/images/marketing/family-hero.webp',about:'/images/marketing/about-family-hero.webp',journey:'/images/marketing/care-journey.webp',portraits:'/images/marketing/care-portraits.webp'};
export const careLinks=[
 {title:'Child Care',copy:'Growth, nutrition, vaccination and every little milestone.',path:'/services/child-care',image:'/images/child.png',theme:'child',icon:Baby},
 {title:"Women's Health",copy:'Thoughtful care for every stage of a woman’s life.',path:'/services/womens-health',image:'/images/women.png',theme:'women',icon:Heart},
 {title:'Adult Health',copy:'Everyday wellbeing, health records and long-term care.',path:'/services/adult-health',image:'/images/adult.png',theme:'adult',icon:Activity},
];

export function MarketingBrand({light=false}:{light?:boolean}){
 return <Link className={'mc-brand'+(light?' mc-brand-light':'')} to="/" aria-label="FamilyCare+ home"><span className="mc-brand-mark" aria-hidden="true"><Plus/></span><span>FamilyCare<span className="mc-brand-plus">+</span></span></Link>;
}
export function MarketingButton({to,children,secondary=false,className=''}:{to:string;children:ReactNode;secondary?:boolean;className?:string}){
 return <Link className={'mc-button '+(secondary?'mc-button-outline ':'')+className} to={to}>{children}<ArrowRight size={17}/></Link>;
}
export function MarketingHeading({eyebrow,title,children}:{eyebrow:string;title:ReactNode;children?:ReactNode}){
 return <div className="mc-section-heading"><span className="mc-eyebrow">{eyebrow}</span><h2>{title}</h2>{children&&<p>{children}</p>}</div>;
}
export function MarketingHeader(){
 const location=useLocation();const [menu,setMenu]=useState(false),[search,setSearch]=useState(false),[query,setQuery]=useState('');
 const dialog=useRef<HTMLDialogElement>(null),searchInput=useRef<HTMLInputElement>(null),toggle=useRef<HTMLButtonElement>(null),services=useRef<HTMLDetailsElement>(null);
 useEffect(()=>{setMenu(false);setSearch(false);if(services.current)services.current.open=false;},[location.pathname,location.hash]);
 useEffect(()=>{
  if(!search){dialog.current?.close();return;}
  const trigger=document.activeElement as HTMLElement|null;dialog.current?.showModal();searchInput.current?.focus();
  const old=document.body.style.overflow;document.body.style.overflow='hidden';
  return()=>{document.body.style.overflow=old;trigger?.focus();};
 },[search]);
 const results=careLinks.filter(c=>(c.title+' '+c.copy).toLowerCase().includes(query.toLowerCase()));
 return <><header className="mc-header"><div className="mc-container mc-header-inner"><MarketingBrand/>
  <button ref={toggle} className="mc-menu-toggle" aria-label={menu?'Close navigation':'Open navigation'} aria-expanded={menu} aria-controls="marketing-navigation" onClick={()=>setMenu(!menu)}>{menu?<X/>:<Menu/>}</button>
  <nav className={'mc-navigation'+(menu?' is-open':'')} id="marketing-navigation" aria-label="Main navigation" onKeyDown={event=>{if(event.key==='Escape'){setMenu(false);toggle.current?.focus();}}}>
   <NavLink end to="/">Home</NavLink><details className="mc-services-menu" ref={services}><summary>Services<ChevronDown size={14}/></summary><div>{careLinks.map(c=><Link to={c.path} key={c.path}><c.icon size={18}/>{c.title}</Link>)}<Link to="/services">All services<ArrowRight size={16}/></Link></div></details>
   <NavLink to="/for-doctors">Doctors</NavLink><NavLink to="/about">About</NavLink><Link to="/#family-care">For Families</Link>
   <Link className="mc-mobile-login" to="/customer/login">Sign in to your account<ArrowRight size={16}/></Link>
  </nav>
  <div className="mc-header-actions"><button className="mc-search-button" aria-label="Search care services" onClick={()=>{setQuery('');setSearch(true);}}><Search size={20}/></button><Link className="mc-sign-in" to="/customer/login">Sign in</Link><MarketingButton to="/customer/login" className="mc-header-book">Book a Visit</MarketingButton></div>
 </div></header>
 <dialog ref={dialog} className="mc-search-dialog" aria-labelledby="marketing-search-title" onCancel={()=>setSearch(false)} onKeyDown={event=>{if(event.key==='Escape'){event.preventDefault();setSearch(false);}}} onClick={event=>{if(event.target===event.currentTarget)setSearch(false);}}><div><button className="mc-dialog-close" aria-label="Close search" onClick={()=>setSearch(false)}><X/></button><span className="mc-eyebrow">FIND YOUR CARE</span><h2 id="marketing-search-title">How can we help your family?</h2><label htmlFor="marketing-search">Search our care services</label><div className="mc-search-field"><Search size={19}/><input ref={searchInput} id="marketing-search" type="search" placeholder="Try child, nutrition or women’s health" value={query} onChange={event=>setQuery(event.target.value)}/></div><div className="mc-search-results">{results.map(c=><Link key={c.path} to={c.path}><c.icon size={22}/><span><strong>{c.title}</strong><small>{c.copy}</small></span><ArrowRight size={18}/></Link>)}{!results.length&&<p>No matching services. Try child, women or adult health.</p>}</div></div></dialog>
 </>;
}

export function MarketingHero({about=false}:{about?:boolean}){
 return <section className={'mc-hero'+(about?' mc-about-hero':'')}>
  <img className="mc-hero-image" src={about?marketingAssets.about:marketingAssets.home} alt={about?'A doctor warmly greeting an older family member with his family beside him':'Three generations of a family sharing a happy moment together'} fetchPriority="high"/>
  <div className="mc-hero-shade"/><div className="mc-container mc-hero-inner"><div className="mc-hero-copy"><span className="mc-eyebrow">{about?'ABOUT US':'CONNECTED FAMILY CARE'}</span>
   <h1>{about?<>Healthcare That<br/>Grows with<br/>Your Family</>:<>Healthcare<br/>for Every{' '}<br/>Generation</>}</h1>
   <p>A comprehensive, compassionate, and connected healthcare platform for you and your family — from little beginnings to every chapter beyond.</p>
   <div className="mc-hero-buttons"><MarketingButton to="/customer/login">Book a Visit</MarketingButton>{!about&&<MarketingButton secondary to="/services">Explore Services</MarketingButton>}</div>
  </div></div>
 </section>;
}

export function MarketingTrustStrip(){
 const features=[{icon:Users,title:<>Care for the<br/>Entire Family</>},{icon:CalendarDays,title:<>Consultation<br/>Requests</>},{icon:FolderHeart,title:<>Your Health<br/>Records, Together</>},{icon:ShieldCheck,title:<>Privacy &<br/>Family Control</>}];
 return <div className="mc-container mc-trust-wrap"><div className="mc-trust-strip">{features.map((f,index)=><div key={index}><span className="mc-dimensional-icon"><f.icon/></span><strong>{f.title}</strong></div>)}</div></div>;
}

export function MarketingServiceCards(){
 return <div className="mc-service-grid">{careLinks.map(c=><Link className={'mc-service-card mc-service-'+c.theme} key={c.path} to={c.path}><img src={c.image} alt="" loading="lazy"/><span className="mc-service-symbol"><c.icon size={26}/></span><div><h3>{c.title}</h3><p>{c.copy}</p><span className="mc-round-arrow" aria-label={'Explore '+c.title}><ArrowRight size={18}/></span></div></Link>)}</div>;
}

export function MarketingVisitBanner(){
 return <section className="mc-container"><div className="mc-visit-banner"><h2>Book Your<br/>Family’s Health Visit Today</h2><CalendarDays/><p>For the little ones and the grown-ups.<br/>Take the next step in your family’s care.</p><MarketingButton to="/customer/login" secondary>Book a Visit</MarketingButton></div></section>;
}

export function MarketingFooter(){
 return <footer className="mc-footer"><svg className="mc-footer-wave" viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true"><path d="M0 34C240-36 371 75 690 30S1180-10 1440 44V80H0Z" fill="currentColor"/></svg><div className="mc-container mc-footer-grid"><div className="mc-footer-brand"><MarketingBrand light/><p>Connected care for every generation.</p></div><div><h3>Quick Links</h3><Link to="/">Home</Link><Link to="/services">Services</Link><Link to="/for-doctors">Doctors</Link></div><div><h3>About</h3><Link to="/about">Our Story</Link><Link to="/about#our-values">Our Values</Link><Link to="/contact">Care & Support</Link></div><div><h3>Support</h3><Link to="/contact">Help & Contact</Link><Link to="/privacy">Privacy Policy</Link><Link to="/terms">Terms & Conditions</Link></div><div><h3>Stay Connected</h3><Link className="mc-footer-contact" to="/contact"><Mail size={19}/>Get in touch</Link><Link to="/customer/login">Family sign in</Link><Link to="/doctor/login">Doctor sign in</Link></div></div><div className="mc-container mc-footer-bottom"><span>© {new Date().getFullYear()} FamilyCare+.</span><span>Thoughtful care. Shared with permission.</span></div></footer>;
}

const everydayStories=[
 {quote:'A child’s growth chart, a parent’s test report, and the next appointment. One place to keep your family’s care connected.',name:'Everyday care, made simpler',detail:'For the whole family',image:'/images/family.png'},
 {quote:'Keep each person’s health story their own. Share selected information with the people you choose, when you choose.',name:'Your family. Your choices.',detail:'Sharing with permission',image:'/images/women.png'},
 {quote:'Bring your saved records and questions together before the next consultation, so important details are easier to find.',name:'Ready for the next conversation',detail:'Records that stay together',image:'/images/adult.png'},
];
export function MarketingStoryCarousel(){
 const [index,setIndex]=useState(0);const item=everydayStories[index];
 return <section className="mc-container mc-everyday"><MarketingHeading eyebrow="MADE FOR REAL FAMILY LIFE" title={<>A little less juggling.<br/>A little more care.</>}/><div className="mc-story-quote" aria-live="polite"><span className="mc-quote-mark" aria-hidden="true">“</span><div><p>{item.quote}</p><strong>{item.name}</strong></div><img src={item.image} alt="" loading="lazy"/><small>{item.detail}</small></div><div className="mc-carousel-controls"><button aria-label="Previous care story" onClick={()=>setIndex((index+everydayStories.length-1)%everydayStories.length)}><ArrowLeft size={20}/></button><button aria-label="Next care story" onClick={()=>setIndex((index+1)%everydayStories.length)}><ArrowRight size={20}/></button></div></section>;
}

export function MarketingCareTeam(){
 const teams=[{title:'Family Medicine',detail:'Care across generations',icon:Users},{title:'Child Health',detail:'Little people, thoughtful care',icon:Baby},{title:"Women’s Wellbeing",detail:'Support for every chapter',icon:Heart},{title:'Adult Care',detail:'A healthier everyday',icon:Stethoscope}];
 return <section className="mc-container mc-section" id="care-team"><div className="mc-heading-row"><MarketingHeading eyebrow="CONNECTED WITH YOUR DOCTOR" title="The Right Care, for Every Chapter"/><MarketingButton secondary to="/for-doctors">For Doctors</MarketingButton></div><div className="mc-team-grid">{teams.map((team,index)=><Link className="mc-team-card" to="/customer/login" key={team.title}><span className={'mc-team-portrait mc-portrait-'+index} style={{backgroundImage:`url(${marketingAssets.portraits})`}} role="img" aria-label={'Illustrative '+team.title.toLowerCase()+' clinician portrait'}/><div><h3>{team.title}</h3><p>{team.detail}</p><span><team.icon size={13}/>Connect with a doctor</span></div><span className="mc-team-arrow"><ArrowRight size={14}/></span></Link>)}</div></section>;
}

type CareArticle={title:string;image:string;link:string;content?:string};
export function MarketingHealthInsights(){
 const fallback:CareArticle[]=[{title:"A parent's guide to child vaccination",image:'/images/child.png',link:'/services/child-care'},{title:"Women's health, through every stage",image:'/images/women.png',link:'/services/womens-health'},{title:'Small steps for your everyday health',image:'/images/adult.png',link:'/services/adult-health'}];
 const [articles,setArticles]=useState<CareArticle[]>(fallback),[selected,setSelected]=useState<CareArticle|null>(null);
 const dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{if(selected){dialog.current?.showModal();const old=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=old;};}dialog.current?.close();},[selected]);
 useEffect(()=>{let active=true;const controller=new AbortController();
  Promise.all(['child','women'].map(audience=>fetch(`${import.meta.env.VITE_API_BASE_URL??''}/api/v1/health-articles?audience=${audience}&per_page=2`,{signal:controller.signal}).then(async response=>{if(!response.ok)return [];const data=await response.json();return Array.isArray(data.items)?data.items:[];}).catch(()=>[]))).then(results=>{
   if(!active)return;const published=results.flat().filter((a:{title?:string;content?:string})=>a.title&&a.content).slice(0,3);
   if(published.length)setArticles(published.map((a:{title:string;content:string;audience:string;cover_image_url?:string})=>({title:a.title,content:a.content,image:a.cover_image_url|| (a.audience==='child'?'/images/child.png':'/images/women.png'),link:'/services/'+(a.audience==='child'?'child-care':'womens-health')})));
  });return()=>{active=false;controller.abort();};
 },[]);
 const card=(article:CareArticle,index:number)=><><img src={article.image} alt="" loading="lazy" onError={event=>{event.currentTarget.onerror=null;event.currentTarget.src=fallback[index%fallback.length].image;}}/><div><h3>{article.title}</h3><span className="mc-round-arrow"><ArrowRight size={14}/></span></div></>;
 return <><section className="mc-container mc-insights"><MarketingHeading eyebrow="HEALTH INSIGHTS" title={<>Tips, Guides & Updates{' '}<br/>for a Healthier Family</>}/><div className="mc-article-grid">{articles.map((article,index)=>article.content?<button className="mc-article" key={article.title+index} onClick={()=>setSelected(article)}>{card(article,index)}</button>:<Link className="mc-article" to={article.link} key={article.title+index}>{card(article,index)}</Link>)}</div><MarketingButton secondary to="/services">Explore Care Guides</MarketingButton></section><dialog ref={dialog} className="mc-article-dialog" aria-labelledby="care-article-title" onCancel={()=>setSelected(null)} onClick={event=>{if(event.target===event.currentTarget)setSelected(null);}}><div><button className="mc-dialog-close" aria-label="Close article" onClick={()=>setSelected(null)}><X/></button><span className="mc-eyebrow">HEALTH INSIGHTS</span><h2 id="care-article-title">{selected?.title}</h2>{selected&&<><img src={selected.image} alt=""/><p className="mc-article-body">{selected.content}</p></>}</div></dialog></>;
}

export const careJourney=[{icon:Leaf,label:'The Beginning',copy:'One simple idea: keep your family’s health story connected.'},{icon:Users,label:'Growing Together',copy:'Separate profiles and care areas, with room for every generation.'},{icon:FolderHeart,label:'A Smarter Everyday',copy:'Reports, measurements and reminders, organized around real life.'},{icon:ShieldCheck,label:'Moving Forward',copy:'Share thoughtfully and stay connected with your care team.'}];
