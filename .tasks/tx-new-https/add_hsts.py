#!/usr/bin/env python3
import pathlib
p = pathlib.Path('/etc/nginx/sites-enabled/yixiaoguan')
t = p.read_text()
marker = 'include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot'
injected = 'add_header Strict-Transport-Security "max-age=31536000" always;'
if injected in t:
    print('HSTS already present')
else:
    n = t.replace(marker, marker + '\n    ' + injected)
    p.write_text(n)
    print(f'HSTS injected into {t.count(marker)} server block(s)')
    zh_female_xinlingjitang_uranus_big tts 换成这个音色吧，然后中间有一句好像有点重叠了，就是两句话的声音有点同时出现，有点冲突，你去找一下。剩下的没什么问题了，修改完以后直接高质量导出吧。