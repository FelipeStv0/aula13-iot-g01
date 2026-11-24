const json=(body:unknown,status=200)=>Response.json(body,{status,headers:{"cache-control":"no-store"}});
const temp=(v:unknown)=>typeof v==="number"&&Number.isFinite(v)&&v>=-55&&v<=125;
Deno.serve(async(req:Request)=>{
 if(req.method!=="POST")return json({error:"method_not_allowed"},405);
 if(Date.now()>=Date.parse("2026-12-24T23:59:59-03:00"))return json({error:"demo_expired"},410);
 let d:Record<string,unknown>;
 try{const raw=await req.text();if(raw.length>2048)return json({error:"too_large"},413);const v=JSON.parse(raw);if(!v||typeof v!=="object"||Array.isArray(v))throw Error();d=v;}catch{return json({error:"invalid_json"},400);}
 if(d.device_id!=="esp32_g01"||typeof d.message_id!=="string"||!/^wokwi-demo-[a-f0-9]{8}-[1-9][0-9]{0,8}$/.test(d.message_id)||d.measurement!=="temperature"||d.unit!=="C"||!temp(d.value)||!temp(d.raw_value)||typeof d.alert!=="string"||!["normal","warning","critical"].includes(d.alert)||typeof d.sample_count!=="number"||!Number.isInteger(d.sample_count)||d.sample_count<1||d.sample_count>3)return json({error:"invalid_payload"},400);
 const url=Deno.env.get("SUPABASE_URL"),key=Deno.env.get("SUPABASE_SECRET_KEY")||Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");if(!url||!key)return json({error:"server_config"},503);
 const h:Record<string,string>={apikey:key,"content-type":"application/json"};if(!key.startsWith("sb_secret_"))h.authorization="Bearer "+key;
 try{const r=await fetch(url.replace(/\/+$/,"")+"/rest/v1/rpc/ingest_wokwi_demo",{method:"POST",headers:h,body:JSON.stringify({p_message_id:d.message_id,p_value:d.value,p_raw_value:d.raw_value,p_alert:d.alert,p_sample_count:d.sample_count})});
 if(!r.ok){console.error("demo RPC",r.status);return json({error:"database_error"},502);}
 const result=await r.json();
 const statuses:Record<string,number>={created:201,duplicate:200,invalid:400,rate:429,quota:429,expired:410};
 return json({result,message_id:d.message_id},statuses[result]??502);
 }catch{return json({error:"database_unavailable"},503);}
});