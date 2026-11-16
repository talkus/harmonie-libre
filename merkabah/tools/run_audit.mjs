import fs from 'node:fs';
import {auditMerkabah} from './audit_integrite.mjs';
const path=process.argv[2];
if(!path){console.error('Usage: node merkabah/tools/run_audit.mjs <file.json> [--strict]');process.exit(2)}
const report=auditMerkabah(JSON.parse(fs.readFileSync(path,'utf8')));
console.log(JSON.stringify(report,null,2));
if(process.argv.includes('--strict')&&report.verdict!=='STRUCTURE_ONLY_NOT_BIBLICAL_VALIDATION')process.exitCode=1;
