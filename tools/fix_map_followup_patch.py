from pathlib import Path

path=Path('tools/patch_map_followup_ux.py')
text=path.read_text(encoding='utf-8')
old="""replace_once(\"  const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);\\n\", '', 'remove dialog move handler')
replace_once(\"  const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);\\n\", '', 'remove desktop dock move handler')
"""
new="""move_line=\"  const move=event.target.closest('[data-popup-move]');if(move)movePopupCard(+move.dataset.popupMove);\\n\"
if text.count(move_line)!=3:
    raise RuntimeError(f'move handlers: expected 3 matches, found {text.count(move_line)}')
text=text.replace(move_line,'',2)
"""
if text.count(old)!=1:
    raise RuntimeError('patch-script move handler block mismatch')
text=text.replace(old,new,1)
old_slice="""desktop=text[text.index(\"document.getElementById('filterOptions').addEventListener\"):text.index(\"document.getElementById('clearFilters')\")]
"""
new_slice="""desktop_start=text.index(\"document.getElementById('filterOptions').addEventListener\")
desktop_end=text.index(\"document.getElementById('clearFilters').addEventListener\",desktop_start)
desktop=text[desktop_start:desktop_end]
"""
if text.count(old_slice)!=1:
    raise RuntimeError('follow-up test desktop wiring slice mismatch')
text=text.replace(old_slice,new_slice,1)
path.write_text(text,encoding='utf-8')
