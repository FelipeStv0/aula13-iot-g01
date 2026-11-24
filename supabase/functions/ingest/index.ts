const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
function equalSecret(a:string,b:string):boolean{const encoder=new TextEncoder();const x=encoder.encode(a);const y=encoder.encode(b);let diff=x.length^y.length;for(let i=0;i<Math.max(x.length,y.length);i++)diff|=(x[i]??0)^(y[i]??0);return diff===0;}
const validId=(v:unknown)=>typeof v==="string"&&/^[A-Za-z0-9_-]{1,50}$/.test(v);
const validTemp=(v:unknown)=>typeof v==="number"&&Number.isFinite(v)&&v>=-55&&v<=125;
Deno.serve(async(request:Request)=>{
 if(request.method!=="POST")return json({error:"method_not_allowed"},405);
 const secret=Deno.env.get("INGEST_KEY"),url=Deno.env.get("SUPABASE_URL")?.replace(/\/+$/,"");
 const key=Deno.env.get("SUPABASE_SECRET_KEY")||Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 if(!secret||!url||!key){console.error("ingest configuration missing",{hasSecret:!!secret,hasUrl:!!url,hasAdminKey:!!key});return json({error:"server_not_configured"},503);}
 if(!equalSecret(request.headers.get("x-ingest-key")??"",secret))return json({error:"unauthorized"},401);
 const declaredLength=Number(request.headers.get("content-length")??0);
 if(declaredLength>8192)return json({error:"body_too_large"},413);
 let data:Record<string,unknown>;
 try{const raw=await request.text();if(new TextEncoder().encode(raw).length>8192)return json({error:"body_too_large"},413);const parsed:unknown=JSON.parse(raw);if(!parsed||typeof parsed!=="object"||Array.isArray(parsed))throw Error("invalid");data=parsed as Record<string,unknown>;}catch{return json({error:"invalid_json"},400);}
 if(!validId(data.device_id)||data.device_id!=="esp32_g01"||typeof data.message_id!=="string"||!/^[A-Za-z0-9_-]{3,80}$/.test(data.message_id)||data.measurement!=="temperature"||data.unit!=="C"||!validTemp(data.value)||!validTemp(data.raw_value)||!["normal","warning","critical"].includes(String(data.alert))||typeof data.sample_count!=="number"||!Number.isInteger(data.sample_count)||data.sample_count<1||data.sample_count>3)return json({error:"invalid_payload"},400);
 const row={device_id:data.device_id,message_id:data.message_id,measurement:"temperature",value:data.value,raw_value:data.raw_value,unit:"C",alert:data.alert,sample_count:data.sample_count};
 const headers:Record<string,string>={"apikey":key,"content-type":"application/json","prefer":"resolution=ignore-duplicates,return=representation"};
 if(!key.startsWith("sb_secret_"))headers.authorization="Bearer "+key;
 let response:Response;
 try{response=await fetch(url+"/rest/v1/readings?on_conflict=device_id,message_id",{method:"POST",headers,body:JSON.stringify(row)});}
 catch(e){console.error("database transport error",String(e));return json({error:"database_unavailable"},503);}
 if(!response.ok){const details=(await response.text()).slice(0,1500);console.error("Database error status:",response.status,"Database response:",details);return json({error:"database_error"},502);}
 let result:unknown;try{result=await response.json();}catch{return json({error:"unexpected_database_response"},502);}
 if(!Array.isArray(result))return json({error:"unexpected_database_response"},502);
 const duplicate=result.length===0;console.log("ingest",String(data.device_id),String(data.message_id),duplicate?"duplicate":"created");
 return json({ok:true,duplicate,message_id:data.message_id,received_at:duplicate?null:(result[0] as {received_at?:string})?.received_at??null},duplicate?200:201);
});