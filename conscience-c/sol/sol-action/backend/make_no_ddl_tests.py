from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'tests.sql').read_text()
a=s.index('do $tests$')
b=s.index('\nselect jsonb_build_object(',a)
s=s[a:b]
s=s.replace("declare j uuid:","declare report jsonb:='[]'; before_counts jsonb; after_counts jsonb; j uuid:",1)
start=s.index('\nbegin\n')
s=s[:start]+'''\nbegin
+ before_counts:=jsonb_build_array((select count(*) from sol_action.jobs),(select count(*) from sol_action.intents),
+  (select count(*) from sol_action.outcomes),(select count(*) from sol_action.events),(select count(*) from sol_action.results),
+  (select count(*) from sol_action_bridge.refusals),(select count(*) from sol_action_bridge.recovery_outcomes));
+ begin
'''.replace('\n+','\n')+s[start+len('\nbegin\n'):]
needle='perform pg_temp.a('
while needle in s:
 st=s.index(needle); pos=st+len(needle); depth=0; quoted=False; vals=[]; last=pos
 while pos<len(s):
  c=s[pos]
  if quoted:
   if c=="'":
    if pos+1<len(s) and s[pos+1]=="'":pos+=2;continue
    quoted=False
  elif c=="'":quoted=True
  elif c=='(':depth+=1
  elif c==')':
   if depth==0:
    vals.append(s[last:pos]);break
   depth-=1
  elif c==',' and depth==0:
   vals.append(s[last:pos]);last=pos+1
  pos+=1
 assert len(vals) in (2,3),vals
 detail=vals[2] if len(vals)==3 else "'{}'::jsonb"
 replacement="report:=report||jsonb_build_array(jsonb_build_object('name',"+vals[0]+",'passed',coalesce(("+vals[1]+"),false),'details',"+detail+"))"
 s=s[:st]+replacement+s[pos+1:]
x=s.index('\nexception when others then\n insert into pg_temp.refusal_assertions')
s=s[:x]+'''
+ raise exception using errcode='ZX001',message='ROLLBACK_ONLY_TEST_FIXTURES';
+ exception when sqlstate 'ZX001' then null;
+ when others then
+  report:=report||jsonb_build_array(jsonb_build_object('name','fatal_error','passed',false,'details',jsonb_build_object('sqlstate',sqlstate,'error',left(sqlerrm,300))));
+ end;
+ after_counts:=jsonb_build_array((select count(*) from sol_action.jobs),(select count(*) from sol_action.intents),
+  (select count(*) from sol_action.outcomes),(select count(*) from sol_action.events),(select count(*) from sol_action.results),
+  (select count(*) from sol_action_bridge.refusals),(select count(*) from sol_action_bridge.recovery_outcomes));
+ report:=report||jsonb_build_array(jsonb_build_object('name','rollback_subtransaction_retained_zero_fixtures','passed',before_counts=after_counts,'details','{}'::jsonb));
+ perform set_config('sol_action.refusal_test_report',report::text,true);
+end $tests$;
'''.replace('\n+','\n')
s=s.replace("denied:=false;begin execute format('truncate sol_action_bridge.%I',tbl);exception when others then denied:=sqlstate='P0001' and sqlerrm='APPEND_ONLY';end;", "denied:=exists(select 1 from pg_trigger where tgrelid=('sol_action_bridge.'||tbl)::regclass and tgname='immutable_truncate' and (tgtype::integer & 32)=32 and tgenabled='O');")
s=s.replace("tbl||'_truncate_denied'", "tbl||'_truncate_trigger_present_without_ddl_execution'")
s='''-- No CREATE/ALTER/DROP or temporary helper. Fixture writes roll back inside the DO subtransaction.
-- Report is a local variable; counters are checked again after the deliberate rollback.
begin;
'''+s+'''
select jsonb_build_object('schema','SOL_ACTION_DURABLE_REFUSAL_SQL_TEST_NO_DDL/v1','observed_at',sol_action.utc(clock_timestamp()),
 'passed',(select count(*) from jsonb_array_elements(current_setting('sol_action.refusal_test_report')::jsonb) a where a->>'passed'='true'),
 'failed',(select count(*) from jsonb_array_elements(current_setting('sol_action.refusal_test_report')::jsonb) a where a->>'passed'='false'),
 'observations',current_setting('sol_action.refusal_test_report')::jsonb,
 'fixture_effects','ALREADY_ROLLED_BACK_IN_DO','worker_execution',false) as result;
rollback;
'''
(p/'tests-no-ddl.sql').write_text(s)
