"use client";
import { useEffect, useState } from "react";
type Food = {name:string;quantity:string|null;kcal:number|null;protein_g:number|null;carbohydrate_g:number|null;fat_g:number|null;nutrition_source:string|null;estimated:boolean};
type Entry = {conversation_id:string;meal_key:string;revision:number;payload:{meal_type:string;foods:Food[]}};
export default function ConsumedMeals({recordDate}:{recordDate:string}) {
  const [state,setState]=useState<{day:string;enabled:boolean;entries:Entry[]}|null>(null);
  const [failed,setFailed]=useState(false);
  useEffect(()=>{
    const controller=new AbortController();
    let active=true;
    async function refresh(){
      try {
        const res=await fetch(`/api/consumed-meals?record_date=${recordDate}`,{cache:"no-store",signal:controller.signal});
        if(!res.ok) throw new Error();
        const data=await res.json();
        if(active){setState({...data,day:recordDate});setFailed(false);}
      } catch {if(active)setFailed(true);}
    }
    const onFocus=()=>{void refresh();};
    window.addEventListener("focus",onFocus);
    void refresh();
    const timer=setInterval(()=>{if(document.visibilityState==="visible")void refresh();},60000);
    return ()=>{active=false;controller.abort();clearInterval(timer);window.removeEventListener("focus",onFocus);};
  },[recordDate]);
  if(failed)return <p role="status">실제 섭취 기록을 불러오지 못했습니다.</p>;
  if(!state?.enabled || state.day!==recordDate)return null;
  return <section className="rounded-xl border border-zinc-700 p-4 my-3">
    <h3 className="font-semibold">대화에서 확인한 실제 섭취</h3>
    <p className="text-xs text-zinc-400">추천 식단과 별도 기록입니다. 기존 직접 입력 합계에는 포함하지 않습니다.</p>
    {!state.entries.length && <p>확인된 섭취 기록이 없습니다.</p>}
    {state.entries.map(e=><div key={`${e.conversation_id}:${e.meal_key}`} className="mt-3">
      <p>{({breakfast:"아침",lunch:"점심",dinner:"저녁",snack:"간식",unknown:"끼니 미확인"} as Record<string,string>)[e.payload.meal_type]}</p>
      {e.payload.foods.map((f,i)=><p key={i}>{f.name} · {f.quantity??"양 미확인"} · {f.kcal==null?"열량 미확인":`${f.kcal} kcal${f.estimated?" (추정)":""}`}<span className="block text-xs text-zinc-400">단백질 {f.protein_g??"미확인"}{f.protein_g!=null?"g":""} · 탄수화물 {f.carbohydrate_g??"미확인"}{f.carbohydrate_g!=null?"g":""} · 지방 {f.fat_g??"미확인"}{f.fat_g!=null?"g":""} · 출처: {f.nutrition_source??"미확인"}</span></p>)}
    </div>)}
  </section>;
}
