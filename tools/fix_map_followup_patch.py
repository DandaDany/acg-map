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
path.write_text(text.replace(old,new,1),encoding='utf-8')
