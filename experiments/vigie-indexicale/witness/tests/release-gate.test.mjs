import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateRelease} from '../release-gate.mjs';
const H='a'.repeat(64),J='b'.repeat(64),D='c'.repeat(64);
const now='2026-10-29T13:00:00Z';
const pins={repo:'synthetic/example',pr:31,head:H,siteId:'test-site',sourceSha:J,deploySha:D};
const base=()=>({schema:'VIGIE-TRIADE-SNAPSHOT-V1',observedAt:now,
 github:{repo:pins.repo,pr:{number:31,head:H,state:'open',draft:true,merged:false},ci:{head:H,conclusion:'success',runId:123,tests:46,failed:0}},
 drive:{source:{sha256:J,bytes:100,shared:false,permissions:['user:owner']},deploy:{sha256:D,bytes:80,shared:false,permissions:['user:owner']}},
 netlify:{siteId:'test-site',requiresSSOTeamLogin:true,deploy:{id:'deploy-1',siteId:'test-site',state:'ready',url:'https://v.test'}},
 browser:{status:'pass',deployId:'deploy-1',origin:'https://v.test'},
 review:{status:'approved',externalRef:'review:ref',subjectRef:'system',reviewerRef:'external'}});
const gate=x=>evaluateRelease(x,{expected:pins,nowISO:now});
const fails=(x,blocker)=>{const r=gate(x);assert.equal(r.ok,false);assert.ok(r.blockers.includes(blocker),JSON.stringify(r));};
test('aucune donnée => refuse sans inventer',()=>fails(null,'SNAPSHOT_INCOMPLET_OU_OBSOLETE'));
test('instant observé inconnu => refuse',()=>{const x=base();delete x.observedAt;fails(x,'SNAPSHOT_INCOMPLET_OU_OBSOLETE')});
test('preuve périmée => refuse',()=>{const x=base();x.observedAt='2026-10-29T10:00:00Z';fails(x,'SNAPSHOT_INCOMPLET_OU_OBSOLETE')});
test('PR head divergent => refuse',()=>{const x=base();x.github.pr.head='f'.repeat(64);fails(x,'GITHUB_PR_OU_COMMIT_NON_CONFORME')});
test('PR prétend fusionnée => refuse',()=>{const x=base();x.github.pr.merged=true;fails(x,'GITHUB_PR_OU_COMMIT_NON_CONFORME')});
test('CI verte mais sur ancien commit => refuse',()=>{const x=base();x.github.ci.head='f'.repeat(64);fails(x,'CI_NON_PROUVEE_SUR_COMMIT')});
test('workflow déclaré mais sans exécution identifiable => refuse',()=>{const x=base();delete x.github.ci.runId;fails(x,'CI_NON_PROUVEE_SUR_COMMIT')});
test('Drive sous partage any reader => refuse',()=>{const x=base();x.drive.source.permissions.push('anyone:reader');fails(x,'DRIVE_OCTETS_OU_CONFIDENTIALITE_NON_ATTESTES')});
test('Drive hash divergent => refuse',()=>{const x=base();x.drive.deploy.sha256='f'.repeat(64);fails(x,'DRIVE_OCTETS_OU_CONFIDENTIALITE_NON_ATTESTES')});
test('Netlify projet sans deploy ID => refuse',()=>{const x=base();x.netlify.deploy={};fails(x,'NETLIFY_DEPLOIEMENT_READY_NON_ATTESTE')});
test('Netlify current n est pas READY => refuse',()=>{const x=base();x.netlify.deploy.state='current';fails(x,'NETLIFY_DEPLOIEMENT_READY_NON_ATTESTE')});
test('Netlify READY d un autre site => refuse',()=>{const x=base();x.netlify.deploy.siteId='elsewhere';fails(x,'NETLIFY_DEPLOIEMENT_READY_NON_ATTESTE')});
test('aperçu navigateur d un autre deploy => refuse',()=>{const x=base();x.browser.deployId='preview-2';fails(x,'NAVIGATEUR_SUR_DEPLOIEMENT_NON_ATTESTE')});
test('navigateur bloqué => refuse',()=>{const x=base();x.browser.status='blocked';fails(x,'NAVIGATEUR_SUR_DEPLOIEMENT_NON_ATTESTE')});
test('auto-évaluation => refuse',()=>{const x=base();x.review.reviewerRef='system';fails(x,'REVUE_HUMAINE_NON_ATTESTEE')});
test('revue non attestée => refuse',()=>{const x=base();x.review.status='unknown';fails(x,'REVUE_HUMAINE_NON_ATTESTEE')});
test('cohérence ne donne jamais la vérité ni autorisation',()=>{const r=gate(base());assert.equal(r.ok,true);assert.equal(r.status,'CANDIDAT_CONCORDANT_NON_AUTORISE');assert.equal(r.authorization,'NOT_ASSESSED');assert.equal(r.epistemic,'E0');assert.equal(r.snapshotAuthenticity,'NOT_ESTABLISHED')});
test('un dossier propriétaire et une CI verte ne compensent pas un deploy absent',()=>{const x=base();x.netlify.deploy={};x.browser={status:'blocked'};const r=gate(x);assert.ok(r.blockers.includes('NETLIFY_DEPLOIEMENT_READY_NON_ATTESTE'));assert.ok(r.blockers.includes('NAVIGATEUR_SUR_DEPLOIEMENT_NON_ATTESTE'))});
test('pins incomplets rejettent même un snapshot complet',()=>{const r=evaluateRelease(base(),{expected:{...pins,head:'x'},nowISO:now});assert.equal(r.ok,false);assert.ok(r.blockers.includes('SNAPSHOT_INCOMPLET_OU_OBSOLETE'))});
