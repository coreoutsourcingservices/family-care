// Child Care includes completed ages 0 through 12; Adult starts at 13.
export function profileAge(dob:string,today=new Date()):number|null {
  if(!/^\d{4}-\d{2}-\d{2}$/.test(dob))return null;
  const [year,month,day]=dob.split('-').map(Number);
  const birth=new Date(year,month-1,day);
  if(birth.getFullYear()!==year||birth.getMonth()!==month-1||birth.getDate()!==day)return null;
  let age=today.getFullYear()-year;
  if(today.getMonth()<month-1||today.getMonth()===month-1&&today.getDate()<day)age--;
  return birth>today?null:age;
}
export function belongsToAdult(dob:string){const age=profileAge(dob);return age!==null&&age>12;}
