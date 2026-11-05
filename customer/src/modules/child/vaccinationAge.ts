/** Calendar months, with month-end birthdays clamped to the last day. */
export function calendarAgeMonths(dob:string,on:string){
 const birth=new Date(dob+'T00:00:00'),date=new Date(on+'T00:00:00');
 if(!Number.isFinite(+birth)||!Number.isFinite(+date)||date<birth)return 0;
 let months=(date.getFullYear()-birth.getFullYear())*12+date.getMonth()-birth.getMonth();
 const anniversary=Math.min(birth.getDate(),new Date(date.getFullYear(),date.getMonth()+1,0).getDate());
 if(date.getDate()<anniversary)months--;
 return Math.max(0,months);
}
export function monthAgeLabel(months:number){
 const years=Math.floor(months/12),remaining=months%12;
 return [years?`${years} ${years===1?'year':'years'}`:'',remaining?`${remaining} ${remaining===1?'month':'months'}`:''].filter(Boolean).join(' ')||'Under 1 month';
}
export function scheduleAgeLabel(label:string,start?:number,end?:number,unit?:string){
 if(/^at birth$/i.test(label)||start===0)return 'At Birth';
 const match=label.match(/^(\d+)(?:\s*[-–]\s*(\d+))?\s*(months?|years?)$/i);
 if(start===undefined&&match){start=Number(match[1]);end=Number(match[2]??match[1]);unit=match[3];}
 if(start===undefined||!unit||!/^months?$|^years?$/i.test(unit))return label;
 const multiplier=/^year/i.test(unit)?12:1;
 const first=monthAgeLabel(start*multiplier),last=monthAgeLabel((end??start)*multiplier);
 return first===last?first:`${first} – ${last}`;
}
