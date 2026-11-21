// Regras transparentes, locais e gratuitas. Nenhum serviço de IA é necessário.
(function(root){
 const median=values=>{const v=[...values].sort((a,b)=>a-b),i=Math.floor(v.length/2);return v.length?(v.length%2?v[i]:(v[i-1]+v[i])/2):null};
 const cost=r=>Number(r.price)+(r.shippingKnown?Number(r.shipping||0):0);
 function profile(p){
  const size=Number(p.sizeInches),hz=Number(p.refresh_hz),panel=String(p.panel||'').toUpperCase(),res=String(p.resolution||'').toUpperCase();
  if(!size||!hz||!panel||!res)return {fit:false,reason:'Especificações incompletas para analisar seu perfil.'};
  if(panel!=='IPS'&&panel!=='FAST IPS')return {fit:false,reason:'Seu perfil exige painel IPS.'};
  if(hz<120)return {fit:false,reason:`${hz} Hz: abaixo dos 120 Hz mínimos que você procura.`};
  if(size>=23.5&&size<=24.5&&res==='1920X1080')return {fit:true,tier:'fhd',reason:'24″ (ou 23,8″), IPS, Full HD e pelo menos 120 Hz.'};
  if(size>=26.5&&size<=27.5&&res==='2560X1440')return {fit:true,tier:'qhd',reason:'27″, IPS, Quad HD e pelo menos 120 Hz.'};
  return {fit:false,reason:'Fora das combinações desejadas: 24″ Full HD ou 27″ Quad HD, com IPS e 120 Hz ou mais.'};
 }
 function eligible(r,allowed){return allowed(r)&&r.condition==='Novo'&&!r.reviewReason&&Number.isFinite(r.price)&&r.price>0&&!r.coupon&&r.kind!=='Excepcional'&&r.availability!=='out_of_stock'}
 function evaluate(p,records,now=new Date(),allowed=()=>false){
  const fit=profile(p),result={...fit,code:'no-fit',label:'Não se adequa',tone:'neutral',reason:fit.reason,historyDays:0,historyCount:0,baseline:null,record:null,price:null,eligible:false};
  if(!fit.fit)return result;
  const today=now.toLocaleDateString('en-CA',{timeZone:'America/Sao_Paulo'});
  const rows=records.filter(r=>r.productId===p.id&&eligible(r,allowed)&&r.date<=today&&Date.parse(r.collectedAt||r.date+'T12:00:00Z')<=now.getTime());
  const latestDate=rows.map(r=>r.date).sort().at(-1);
  const latest=rows.filter(r=>r.date===latestDate).sort((a,b)=>cost(a)-cost(b))[0];
  if(!latest)return {...result,code:'no-offer',label:'Sem oferta para analisar',reason:fit.reason+' Falta um anúncio novo das lojas permitidas.'};
  const price=cost(latest),age=(now-Date.parse(latest.collectedAt||latest.date+'T12:00:00Z'))/3600000;
  // Só compara períodos anteriores, com a mesma condição de frete. Um dia não cria histórico habitual.
  const groups=new Map();
  for(const r of rows.filter(r=>r.date<latest.date&&Boolean(r.shippingKnown)===Boolean(latest.shippingKnown))){const key=r.date+'|'+r.store;groups.set(key,[...(groups.get(key)||[]),cost(r)])}
  const values=[...groups.values()].map(median),mid=median(values),regular=mid===null?[]:values.filter(v=>v>=mid*.5&&v<=mid*1.5);
  const days=new Set([...groups.keys()].map(k=>k.slice(0,10))).size,baseline=median(regular),enough=days>=3&&regular.length>=3;
  const priorBF=rows.filter(r=>r.date<latest.date&&r.date.slice(0,4)<latest.date.slice(0,4)&&r.kind==='Black Friday');
  const base={...result,record:latest,price,historyDays:days,historyCount:regular.length,baseline:enough?baseline:null,previousBF:priorBF.length,ageHours:age,eligible:age<=96&&price<=1000};
  const shipping=latest.shippingKnown?'Frete incluído.':'Frete a confirmar: o total precisa permanecer em até R$ 1.000.';
  if(price>1000)return {...base,eligible:false,code:'over-budget',label:'Acima do orçamento',tone:'bad',reason:`Ultrapassa o teto de R$ 1.000 em R$ ${(price-1000).toFixed(2).replace('.',',')}, mesmo antes de eventual frete.`};
  if(age>96)return {...base,eligible:false,code:'stale',label:'Preço precisa de atualização',tone:'neutral',reason:'Última verificação há mais de 96 horas. Confira preço e estoque antes de decidir.'};
  if(enough&&price<baseline*.5)return {...base,eligible:false,code:'outlier',label:'Preço atípico · verificar',tone:'warning',reason:'Mais de 50% abaixo da mediana anterior. Pode exigir cupom ou ter condições diferentes; não é sinal automático de compra.'};
  if(enough&&price>baseline*1.10)return {...base,code:'expensive',label:'Caro frente ao histórico',tone:'bad',reason:`Mais de 10% acima da mediana anterior de ${days} dias. ${shipping}`};
  const atTarget=Number(p.target)>0&&price<=Number(p.target),drop=enough?(baseline-price)/baseline:0;
  if(atTarget&&enough&&latest.shippingKnown)return {...base,code:'ideal',label:'Ponto ideal pelos seus critérios',tone:'good',reason:`Meta atingida, total dentro do teto e referência de ${days} dias. Ainda confira estoque e vendedor.`,qhdValue:true};
  if(atTarget||drop>=.10)return {...base,code:'opportunity',label:atTarget?'Meta atingida · boa oportunidade':'Boa oportunidade no histórico',tone:'good',reason:(atTarget?'Preço dentro da sua meta. ':`${(drop*100).toFixed(1)}% abaixo da mediana anterior. `)+(enough?'':'Histórico inicial: não confirma menor preço de Black Friday. ')+shipping,qhdValue:atTarget||drop>=.10};
  return {...base,code:'fits',label:enough?'Dentro do perfil':'Dentro do perfil · histórico inicial',tone:'info',reason:fit.reason+' '+(enough?'Sem queda de pelo menos 10% frente à mediana anterior. ':'Ainda não há três dias anteriores comparáveis para avaliar a oportunidade. ')+shipping,qhdValue:false};
 }
 function rank(products,records,now,allowed){
  const entries=products.map(p=>({p,a:evaluate(p,records,now,allowed)}));
  const valid=entries.filter(x=>x.a.fit&&x.a.eligible&&!['expensive','outlier'].includes(x.a.code));
  const fhd=valid.filter(x=>x.a.tier==='fhd').sort((x,y)=>x.a.price-y.a.price);
  const qhd=valid.filter(x=>x.a.tier==='qhd').sort((x,y)=>x.a.price-y.a.price);
  // QHD só substitui a opção econômica quando atinge a meta ou há queda histórica relevante.
  const premium=qhd.find(x=>x.a.qhdValue),best=premium||fhd[0]||qhd[0]||null;
  if(fhd[0])for(const x of entries){if(x.a.tier==='fhd'&&x.a.eligible&&x.a.price>=fhd[0].a.price*1.2&&x.a.price-fhd[0].a.price>=100&&x!==fhd[0]){x.a={...x.a,code:'costly-alternative',label:'Custo-benefício inferior hoje',tone:'warning',reason:`Custa pelo menos 20% e R$ 100 a mais que ${fhd[0].p.name}, que também atende ao perfil de 24″. Taxa extra de Hz não recebe prioridade sobre preço.`}}}
  return {best,alternative:best?.a.tier==='qhd'?fhd[0]||null:qhd[0]||null,entries};
 }
 const api={profile,evaluate,rank};if(typeof module!=='undefined')module.exports=api;else root.PurchaseAnalysis=api;
})(typeof window!=='undefined'?window:this);
