from pathlib import Path
import re

ROOT=Path('.')
HTML=ROOT/'public'/'taiwan-exhibition-map.html'
DECISION=ROOT/'decision.md'
MAP_TEST=ROOT/'backend'/'_test_map_ux.py'
HOME_TEST=ROOT/'backend'/'_test_editorial_c_home.py'
NEW_TEST=ROOT/'backend'/'_test_map_exploration_polish.py'
text=HTML.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global text
    c=text.count(old)
    if c!=1:
        raise RuntimeError(f'{label}: expected 1 match, found {c}')
    text=text.replace(old,new,1)

def sub_once(pattern,repl,label,flags=0):
    global text
    text2,c=re.subn(pattern,repl,text,count=1,flags=flags)
    if c!=1:
        raise RuntimeError(f'{label}: expected 1 regex match, found {c}')
    text=text2

# ---------------------------------------------------------------------------
# 3. Activity-time filter = status OR a calendar date. No Today/Weekend/Next7.
# ---------------------------------------------------------------------------
replace_once(
"""  time:{title:'時間',defaultLabel:'全部時間',options:[
    {value:'all',label:'全部時間'},{value:'next7',label:'未來 7 天'},{value:'today',label:'今天'},{value:'weekend',label:'本週末'},
    {value:'ongoing',label:'進行中'},{value:'upcoming',label:'即將開始'},{value:'ending',label:'即將結束'}]},""",
"""  time:{title:'活動時段',defaultLabel:'不限',options:[
    {value:'all',label:'不限'},{value:'ongoing',label:'進行中'},
    {value:'upcoming',label:'即將開始'},{value:'ending',label:'即將結束'}]},""",
'activity time filter metadata')
replace_once(
'<button class="filter-category" type="button" data-filter="time" aria-expanded="false"><span class="filter-icon" aria-hidden="true">◷</span><span class="filter-name">時間</span><span class="filter-value" data-filter-value="time">全部時間</span><span class="filter-arrow" aria-hidden="true">›</span></button>',
'<button class="filter-category" type="button" data-filter="time" aria-expanded="false"><span class="filter-icon" aria-hidden="true">◷</span><span class="filter-name">活動時段</span><span class="filter-value" data-filter-value="time">不限</span><span class="filter-arrow" aria-hidden="true">›</span></button>',
'activity time filter label')
sub_once(
 r"function currentWeekendRange\(today=taipeiCalendarToday\(\)\)\{.*?\n\}\n",
 '',
 'remove weekend helper',
 re.S)
replace_once(
"""function locationMatchesTimeFilter(location,value){
  if(value==='today'){const day=calendarDayNumber(taipeiCalendarToday());return locationOverlapsCalendarRange(location,day,day)}
  if(value==='next7'){const day=calendarDayNumber(taipeiCalendarToday());return locationOverlapsCalendarRange(location,day,day+6)}
  if(value==='weekend'){const range=currentWeekendRange();return locationOverlapsCalendarRange(location,range.start,range.end)}
  return location.status.kind===value||(value==='ongoing'&&location.status.kind==='ending');
}""",
"""function timeFilterDate(value){const match=String(value||'').match(/^date:(\\d{4}-\\d{2}-\\d{2})$/);return match?match[1]:''}
function locationActiveOnCalendarDay(location,day){
  const start=eventCalendarDayNumber(location.start),end=eventCalendarDayNumber(location.end);
  if(Number.isFinite(start)&&day<start)return false;
  if(Number.isFinite(end)&&day>end)return false;
  return Number.isFinite(start)||Number.isFinite(end)||location.status.kind==='ongoing'||location.status.kind==='ending';
}
function locationMatchesTimeFilter(location,value){
  const selectedDate=timeFilterDate(value);
  if(selectedDate){const day=calendarDayNumber(selectedDate);return Number.isFinite(day)&&locationActiveOnCalendarDay(location,day)}
  if(value==='all')return true;
  return location.status.kind===value;
}""",
'calendar time matching')

# ---------------------------------------------------------------------------
# 2. Recent-discovery filter facets are based on the latest 7-day base set.
# ---------------------------------------------------------------------------
replace_once(
"""function getFacetCount(key,value,state=uiState){
  const filters={...state.filters,[key]:value};
  if(key==='multi'){
    const groups=[...activityGroups.values()].filter(group=>
      group.status.kind!=='ended'&&group.multiFilter&&(value==='all'||group.multiFilter===value)
      &&groupMatchesFilters(group,filters,'multi')&&groupMatchesQuery(group,state.query)
    );
    return groups.reduce((sum,group)=>sum+group.locations.filter(location=>occurrenceVisible(location,filters)).length,0);
  }
  return [...activityGroups.values()].filter(group=>
    group.status.kind!=='ended'&&groupMatchesFilters(group,filters,'')&&groupMatchesQuery(group,state.query)
  ).length;
}""",
"""function facetBaseGroups(state=uiState){
  let groups=[...activityGroups.values()].filter(group=>group.status.kind!=='ended');
  if(state.exploreView==='collection'&&state.collectionContext==='latest')groups=groups.filter(group=>isLatestGroup(group));
  return groups;
}
function getFacetCount(key,value,state=uiState){
  const filters={...state.filters,[key]:value};
  const base=facetBaseGroups(state);
  if(key==='multi'){
    const groups=base.filter(group=>
      group.multiFilter&&(value==='all'||group.multiFilter===value)
      &&groupMatchesFilters(group,filters,'multi')&&groupMatchesQuery(group,state.query)
    );
    return groups.reduce((sum,group)=>sum+group.locations.filter(location=>occurrenceVisible(location,filters)).length,0);
  }
  return base.filter(group=>groupMatchesFilters(group,filters,'')&&groupMatchesQuery(group,state.query)).length;
}""",
'latest-scoped facet counts')

# ---------------------------------------------------------------------------
# Calendar UI shared by desktop + mobile filter detail.
# ---------------------------------------------------------------------------
replace_once(
"""function filterOptionLabel(key,value){
  const item=filterOptionsFor(key).find(option=>option.value===value);
  return item?item.label:FILTER_META[key].defaultLabel;
}
let openFilterKey='';""",
"""function filterOptionLabel(key,value){
  if(key==='time'){
    const date=timeFilterDate(value);
    if(date){const day=calendarDayNumber(date);return Number.isFinite(day)?formatMonthDay(day):FILTER_META[key].defaultLabel}
  }
  const item=filterOptionsFor(key).find(option=>option.value===value);
  return item?item.label:FILTER_META[key].defaultLabel;
}
let filterCalendarMonth='';
function initialFilterCalendarMonth(state=uiState){
  const selected=timeFilterDate(state.filters.time);
  return (selected||taipeiCalendarToday()).slice(0,7);
}
function calendarMonthDay(month){return calendarDayNumber(month+'-01')}
function shiftCalendarMonth(month,delta){
  const day=calendarMonthDay(month);if(!Number.isFinite(day))return initialFilterCalendarMonth();
  const date=new Date(day*86400000);date.setUTCMonth(date.getUTCMonth()+delta);
  return date.getUTCFullYear()+'-'+String(date.getUTCMonth()+1).padStart(2,'0');
}
function filterCalendarMaxDay(state=uiState){
  const today=calendarDayNumber(taipeiCalendarToday());let max=today;let hasOpenEnded=false;
  facetBaseGroups(state).forEach(group=>group.locations.forEach(location=>{
    const candidate=eventCalendarDayNumber(location.end||location.start);if(Number.isFinite(candidate))max=Math.max(max,candidate);
    if(!location.end&&(location.status.kind==='ongoing'||location.status.kind==='ending'))hasOpenEnded=true;
  }));
  return hasOpenEnded?Math.max(max,today+365):max;
}
function filterCalendarHtml(state=uiState){
  if(!filterCalendarMonth)filterCalendarMonth=initialFilterCalendarMonth(state);
  const first=calendarMonthDay(filterCalendarMonth),today=calendarDayNumber(taipeiCalendarToday()),maxDay=filterCalendarMaxDay(state);
  const firstDate=new Date(first*86400000),year=firstDate.getUTCFullYear(),month=firstDate.getUTCMonth();
  const daysInMonth=new Date(Date.UTC(year,month+1,0)).getUTCDate();
  const offset=(firstDate.getUTCDay()+6)%7;
  const selected=timeFilterDate(state.filters.time);
  const cells=[];
  for(let i=0;i<42;i++){
    const dayNumber=i-offset+1;
    if(dayNumber<1||dayNumber>daysInMonth){cells.push('<span class="filter-calendar-spacer"></span>');continue}
    const iso=year+'-'+String(month+1).padStart(2,'0')+'-'+String(dayNumber).padStart(2,'0');
    const absolute=calendarDayNumber(iso),count=getFacetCount('time','date:'+iso,state),isSelected=selected===iso,isToday=absolute===today;
    const disabled=(absolute<today||absolute>maxDay||count===0)&&!isSelected;
    cells.push('<button class="filter-calendar-day'+(isSelected?' selected':'')+(isToday?' today':'')+(count>0?' has-events':'')+'" type="button" data-calendar-date="'+iso+'" '+(disabled?'disabled':'')+' aria-pressed="'+(isSelected?'true':'false')+'" aria-label="'+(month+1)+' 月 '+dayNumber+' 日"><span>'+dayNumber+'</span><i aria-hidden="true"></i></button>');
  }
  const prevMonth=shiftCalendarMonth(filterCalendarMonth,-1),nextMonth=shiftCalendarMonth(filterCalendarMonth,1);
  const prevDisabled=calendarMonthDay(prevMonth)<calendarMonthDay(taipeiCalendarToday().slice(0,7));
  const nextDisabled=calendarMonthDay(nextMonth)>calendarMonthDay(new Date(maxDay*86400000).getUTCFullYear()+'-'+String(new Date(maxDay*86400000).getUTCMonth()+1).padStart(2,'0'));
  return '<section class="filter-calendar" aria-label="選擇活動日期"><div class="filter-calendar-label">選擇日期</div><div class="filter-calendar-head"><button type="button" data-calendar-shift="-1" '+(prevDisabled?'disabled':'')+' aria-label="上一個月">‹</button><strong>'+year+' 年 '+(month+1)+' 月</strong><button type="button" data-calendar-shift="1" '+(nextDisabled?'disabled':'')+' aria-label="下一個月">›</button></div><div class="filter-calendar-weekdays"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div><div class="filter-calendar-grid">'+cells.join('')+'</div></section>';
}
let openFilterKey='';""",
'filter calendar helpers')

replace_once(
"""function renderDesktopFilterOptions(){
  if(!openFilterKey) return;
  const root=document.getElementById('filterOptions');
  root.innerHTML=filterOptionsFor(openFilterKey).map(option=>{
    if(option.group) return '<div class="filter-group">'+esc(option.group)+'</div>';
    const count=getFacetCount(openFilterKey,option.value);
    const selected=uiState.filters[openFilterKey]===option.value;
    const disabled=count===0&&!selected;
    return '<button class="filter-option'+(selected?' selected':'')+'" type="button" data-value="'+esc(option.value)+'" '+(disabled?'disabled':'')+' aria-pressed="'+(selected?'true':'false')+'">'
      +'<span class="filter-check">✓</span><span>'+esc(option.label)+'</span><span class="filter-count">'+count+'</span></button>';
  }).join('');
}""",
"""function renderDesktopFilterOptions(){
  if(!openFilterKey) return;
  const root=document.getElementById('filterOptions');
  const options=filterOptionsFor(openFilterKey).map(option=>{
    if(option.group) return '<div class="filter-group">'+esc(option.group)+'</div>';
    const count=getFacetCount(openFilterKey,option.value);
    const selected=uiState.filters[openFilterKey]===option.value;
    const disabled=count===0&&!selected;
    return '<button class="filter-option'+(selected?' selected':'')+'" type="button" data-value="'+esc(option.value)+'" '+(disabled?'disabled':'')+' aria-pressed="'+(selected?'true':'false')+'">'
      +'<span class="filter-check">✓</span><span>'+esc(option.label)+'</span><span class="filter-count">'+count+'</span></button>';
  }).join('');
  root.innerHTML=options+(openFilterKey==='time'?filterCalendarHtml(uiState):'');
}""",
'desktop calendar rendering')
replace_once(
"""function openFilterDetail(key){
  openFilterKey=key;
  document.getElementById('filterDetailTitle').textContent=FILTER_META[key].title;""",
"""function openFilterDetail(key){
  openFilterKey=key;if(key==='time'&&!filterCalendarMonth)filterCalendarMonth=initialFilterCalendarMonth(uiState);
  document.getElementById('filterDetailTitle').textContent=FILTER_META[key].title;""",
'calendar month on desktop open')
replace_once(
"function mobileFilterState(){return {query:uiState.query,filters:draftFilters||uiState.filters}}",
"function mobileFilterState(){return {query:uiState.query,filters:draftFilters||uiState.filters,exploreView:uiState.exploreView,collectionContext:uiState.collectionContext}}",
'mobile filter context')
replace_once(
"""function renderMobileFilterOptions(key){
  mobileFilterKey=key;
  document.getElementById('mobileFilterTitle').textContent=FILTER_META[key].title;
  document.getElementById('mobileFilterBack').hidden=false;
  const state=mobileFilterState();
  const root=document.getElementById('mobileFilterContent');
  root.innerHTML=filterOptionsFor(key).map(option=>{
    if(option.group) return '<div class="filter-group">'+esc(option.group)+'</div>';
    const count=getFacetCount(key,option.value,state);
    const selected=state.filters[key]===option.value;
    const disabled=count===0&&!selected;
    return '<button class="filter-option'+(selected?' selected':'')+'" type="button" data-mobile-value="'+esc(option.value)+'" '+(disabled?'disabled':'')+' aria-pressed="'+(selected?'true':'false')+'">'
      +'<span class="filter-check">✓</span><span>'+esc(option.label)+'</span><span class="filter-count">'+count+'</span></button>';
  }).join('');
}""",
"""function renderMobileFilterOptions(key){
  mobileFilterKey=key;
  document.getElementById('mobileFilterTitle').textContent=FILTER_META[key].title;
  document.getElementById('mobileFilterBack').hidden=false;
  const state=mobileFilterState();if(key==='time'&&!filterCalendarMonth)filterCalendarMonth=initialFilterCalendarMonth(state);
  const root=document.getElementById('mobileFilterContent');
  const options=filterOptionsFor(key).map(option=>{
    if(option.group) return '<div class="filter-group">'+esc(option.group)+'</div>';
    const count=getFacetCount(key,option.value,state);
    const selected=state.filters[key]===option.value;
    const disabled=count===0&&!selected;
    return '<button class="filter-option'+(selected?' selected':'')+'" type="button" data-mobile-value="'+esc(option.value)+'" '+(disabled?'disabled':'')+' aria-pressed="'+(selected?'true':'false')+'">'
      +'<span class="filter-check">✓</span><span>'+esc(option.label)+'</span><span class="filter-count">'+count+'</span></button>';
  }).join('');
  root.innerHTML=options+(key==='time'?filterCalendarHtml(state):'');
}""",
'mobile calendar rendering')

replace_once(
"""document.getElementById('filterOptions').addEventListener('click',event=>{
  const button=event.target.closest('[data-value]');if(!button||button.disabled||!openFilterKey)return;
  const key=openFilterKey,value=button.dataset.value;uiState.filters[key]=value;closeFilterDetail();renderAll();if(key==='city'&&uiState.exploreView==='results')fitCityView(value);
});""",
"""document.getElementById('filterOptions').addEventListener('click',event=>{
  const shift=event.target.closest('[data-calendar-shift]');if(shift&&!shift.disabled){filterCalendarMonth=shiftCalendarMonth(filterCalendarMonth,+shift.dataset.calendarShift);renderDesktopFilterOptions();return}
  const day=event.target.closest('[data-calendar-date]');if(day&&!day.disabled){uiState.filters.time='date:'+day.dataset.calendarDate;filterCalendarMonth=day.dataset.calendarDate.slice(0,7);closeFilterDetail();renderAll();return}
  const button=event.target.closest('[data-value]');if(!button||button.disabled||!openFilterKey)return;
  const key=openFilterKey,value=button.dataset.value;uiState.filters[key]=value;closeFilterDetail();renderAll();if(key==='city'&&uiState.exploreView==='results')fitCityView(value);
});""",
'desktop calendar events')
replace_once(
"""document.getElementById('mobileFilterContent').addEventListener('click',event=>{
  const category=event.target.closest('[data-mobile-filter]');if(category){renderMobileFilterOptions(category.dataset.mobileFilter);return}
  const option=event.target.closest('[data-mobile-value]');if(option&&!option.disabled&&mobileFilterKey){draftFilters[mobileFilterKey]=option.dataset.mobileValue;renderMobileFilterOptions(mobileFilterKey)}
});""",
"""document.getElementById('mobileFilterContent').addEventListener('click',event=>{
  const category=event.target.closest('[data-mobile-filter]');if(category){renderMobileFilterOptions(category.dataset.mobileFilter);return}
  const shift=event.target.closest('[data-calendar-shift]');if(shift&&!shift.disabled){filterCalendarMonth=shiftCalendarMonth(filterCalendarMonth,+shift.dataset.calendarShift);renderMobileFilterOptions('time');return}
  const day=event.target.closest('[data-calendar-date]');if(day&&!day.disabled){draftFilters.time='date:'+day.dataset.calendarDate;filterCalendarMonth=day.dataset.calendarDate.slice(0,7);renderMobileFilterOptions('time');return}
  const option=event.target.closest('[data-mobile-value]');if(option&&!option.disabled&&mobileFilterKey){draftFilters[mobileFilterKey]=option.dataset.mobileValue;renderMobileFilterOptions(mobileFilterKey)}
});""",
'mobile calendar events')

# Remove obsolete Today/Weekend empty-state behavior from hidden legacy list.
sub_once(
 r"    \}else\{\n      const time=uiState\.filters\.time;\n      const message=time==='today'.*?\n      if\(time==='today'\)document\.getElementById\('emptyWeekend'\).*?\n    \}",
 """    }else{
      list.innerHTML='<div class=\"empty-state\"><div><p>沒有符合條件的活動</p><div class=\"empty-actions\"><button class=\"secondary-btn\" id=\"emptyClear\" type=\"button\">清除篩選</button></div></div></div>';
      document.getElementById('emptyClear').addEventListener('click',clearAllFilters);
    }""",
 'remove obsolete quick-date empty state',re.S)

HTML.write_text(text,encoding='utf-8')
