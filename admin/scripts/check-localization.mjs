import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {uiKeys} from './localization-keys.mjs';
const root=new URL('../../',import.meta.url),catalogRoot=new URL('backend/locales/',root);
const en=JSON.parse(readFileSync(new URL('en.json',catalogRoot),'utf8'));
const tokens=value=>(value.match(/\{\{.*?\}\}/g)||[]).sort();
for(const key of uiKeys())assert.ok(key in en,'English catalog missing '+key);
let count=0;
for(const file of readdirSync(catalogRoot).filter(f=>f.endsWith('.json'))){const catalog=JSON.parse(readFileSync(new URL(file,catalogRoot),'utf8'));assert.deepEqual(Object.keys(catalog).sort(),Object.keys(en).sort(),file+' key coverage');for(const key in en){assert.ok(typeof catalog[key]==='string'&&catalog[key].trim(),file+': '+key);assert.deepEqual(tokens(catalog[key]),tokens(en[key]),file+' interpolation: '+key);}count++;}
console.log(`PASS ${count} catalogs, ${Object.keys(en).length} keys, UI coverage and interpolation tokens`);
