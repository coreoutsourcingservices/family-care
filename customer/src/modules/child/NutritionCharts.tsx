import {useEffect,useRef} from 'react';
import {Chart,PieController,ArcElement,BarController,BarElement,CategoryScale,LinearScale,Tooltip,Legend} from 'chart.js';
import {localDate,type ChildEntry} from './childRecords';
Chart.register(PieController,ArcElement,BarController,BarElement,CategoryScale,LinearScale,Tooltip,Legend);
export default function NutritionCharts({entries}:{entries:ChildEntry[]}){
 const pie=useRef<HTMLCanvasElement>(null),bar=useRef<HTMLCanvasElement>(null);
 const meals=entries.filter(e=>e.kind==='nutrition');
 const types=['Breakfast','Lunch','Dinner','Snack','Milk / feeding','Other'];
 const counts=types.map(type=>meals.filter(e=>(types.includes(e.meal)?e.meal:'Other')===type).length);
 const days=Array.from({length:7},(_,i)=>{const d=new Date(localDate()+'T00:00:00');d.setDate(d.getDate()-6+i);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;});
 const recent=days.map(date=>meals.filter(e=>e.date===date).length);
 useEffect(()=>{if(!meals.length||!pie.current||!bar.current)return;
  const animation=window.matchMedia('(prefers-reduced-motion: reduce)').matches?false:undefined;
  const first=new Chart(pie.current,{type:'pie',data:{labels:types,datasets:[{data:counts,backgroundColor:['#3395ff','#63cdbb','#9e83ef','#ff9ab9','#ffc56f','#c4d7ec'],borderWidth:3,borderColor:'#fff'}]},options:{responsive:true,maintainAspectRatio:false,animation,plugins:{legend:{position:'bottom',labels:{boxWidth:9,padding:10,font:{size:10}}}}}});
  const second=new Chart(bar.current,{type:'bar',data:{labels:days.map(date=>new Date(date+'T00:00:00').toLocaleDateString('en-IN',{weekday:'short'})),datasets:[{label:'Meal notes',data:recent,backgroundColor:'#65c7ba',borderRadius:6,maxBarThickness:28}]},options:{responsive:true,maintainAspectRatio:false,animation,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{precision:0},title:{display:true,text:'Notes logged'}},x:{grid:{display:false}}}}});
  return()=>{first.destroy();second.destroy();};
 },[entries]);
 return <div className="nutrition-charts"><p className="nutrition-chart-caption">Meal logging overview · based on your saved notes</p><div className="nutrition-chart-grid"><section><h3>Meal types</h3><div className="nutrition-chart-canvas">{meals.length?<canvas ref={pie} role="img" aria-label="Meal type pie chart"/>:<p>No meal notes yet.<br/>Add a meal to start your pie chart.</p>}</div></section><section><h3>Last 7 days</h3><div className="nutrition-chart-canvas">{meals.length?<canvas ref={bar} role="img" aria-label="Daily meal notes bar chart"/>:<p>Your daily meal notes will appear here.</p>}</div></section></div><details><summary>View nutrition chart values</summary><dl>{types.map((type,i)=><div key={type}><dt>{type}</dt><dd>{counts[i]} notes</dd></div>)}</dl><p>Last 7 days: {recent.reduce((a,b)=>a+b,0)} meal notes. Charts count entries; they do not estimate nutrients or calories.</p></details></div>;
}
