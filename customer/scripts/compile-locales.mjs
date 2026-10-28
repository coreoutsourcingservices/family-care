// The requested Node i18n package prepares static catalogs; no Node code ships to browsers.
import {I18n} from 'i18n';
import {readFile,readdir,mkdir,writeFile} from 'node:fs/promises';
const source=new URL('../src/localization/source/',import.meta.url);
const output=new URL('../src/localization/compiled/',import.meta.url);
const catalogs={};
for(const name of await readdir(source)){if(name.endsWith('.json'))catalogs[name.slice(0,-5)]=JSON.parse(await readFile(new URL(name,source),'utf8'));}
const keys=Object.keys(catalogs.en);
const i18n=new I18n({locales:Object.keys(catalogs),defaultLocale:'en',staticCatalog:catalogs,objectNotation:false,updateFiles:false});
await mkdir(output,{recursive:true});
for(const locale of Object.keys(catalogs)){
 const missing=keys.filter(key=>typeof catalogs[locale][key]!=='string'||!catalogs[locale][key].trim());
 if(missing.length)throw Error(locale+' has '+missing.length+' missing translations');
 const compiled=Object.fromEntries(keys.map(phrase=>[phrase,i18n.__({phrase,locale})]));
 await writeFile(new URL(locale+'.json',output),JSON.stringify(compiled,null,2)+'\n');
}
console.log('Compiled '+Object.keys(catalogs).length+' customer catalogs with i18n.');
