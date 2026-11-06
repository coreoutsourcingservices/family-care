import ts from 'typescript';
import {readFileSync,readdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
export function uiKeys(){
 const keys=new Set(Object.keys(JSON.parse(readFileSync(path.join(root,'admin/src/locales/en.json'),'utf8'))));
 const files=readdirSync(path.join(root,'admin/src/components')).filter(f=>f.endsWith('.tsx')).map(f=>'admin/src/components/'+f).concat(['app/src/components/WomenArticleManager.tsx']);
 for(const file of files){const sf=ts.createSourceFile(file,readFileSync(path.join(root,file),'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  function visit(n){if(ts.isStringLiteral(n)){const value=n.text,p=n.parent;
   const translated=ts.isCallExpression(p)&&/^(t|translateUi)$/.test(p.expression.getText(sf))&&p.arguments[0]===n;
   const helper=ts.isCallExpression(p)&&/^(input|select|check)$/.test(p.expression.getText(sf))&&p.arguments[3]===n;
   const property=ts.isPropertyAssignment(p)&&/^(label|title|text|description)$/.test(p.name.getText(sf));
   let labels=false;for(let a=p;a;a=a.parent){if(ts.isVariableDeclaration(a)){labels=/labels|roles/i.test(a.name.getText(sf));break;}if(ts.isFunctionDeclaration(a))break;}
   const array=ts.isArrayLiteralExpression(p)&&(/^[A-Z][A-Za-z &/()'-]*$/.test(value)||['days','weeks','months','years'].includes(value));
   const message=ts.isCallExpression(p)&&/^(setError|setNotice|setReviewError|setActionError|confirm|prompt)$/.test(p.expression.getText(sf));
   if((translated||helper||property||labels||array||message)&&/[A-Za-z]/.test(value)&&value.trim())keys.add(value);
  }ts.forEachChild(n,visit);}visit(sf);
 }
 return [...keys].sort();
}
if(process.argv[1]===fileURLToPath(import.meta.url))process.stdout.write(JSON.stringify(uiKeys(),null,2)+'\n');
