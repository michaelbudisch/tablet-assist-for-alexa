const CSS="\n.hz-ambient-head,.hz-ambient-stage{transition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .7s ease;will-change:transform}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-head{transform:translateY(-10px) scale(.91);transform-origin:50% 0}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-stage{transform:translate3d(0,-13vh,0) scale(.62);opacity:.72;transform-origin:50% 8%}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-foot{opacity:0}\n.hz-overview{position:absolute;inset:clamp(225px,36vh,380px) 12px 12px;z-index:6;\ndisplay:flex;flex-direction:column;box-sizing:border-box;min-height:140px;overflow:hidden;padding:11px 12px;\nbackground:linear-gradient(180deg,#10304ae8,#0a1b34f7 68%,#081728f7);\ncolor:#eff8ff;border:1px solid #77d1ed6a;border-radius:17px;box-shadow:0 22px 50px #030b1ad6,0 0 30px #34d7e329;\nbackdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);\nopacity:0;visibility:hidden;pointer-events:none;transform:translate3d(0,107%,0);\ntransition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .55s ease,visibility 0s linear .85s}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview{opacity:1;visibility:visible;pointer-events:auto;\ntransform:translate3d(0,0,0);transition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .55s ease}\n.hz-ambient-body[data-overview=\"open\"]::after{content:\"\";position:absolute;z-index:4;left:50%;top:26%;\nwidth:min(75vw,540px);aspect-ratio:1;border:1.5px solid #64e5f2;border-radius:50%;pointer-events:none;\nanimation:hz-overview-ripple .85s ease-out both;box-shadow:0 0 16px #47daed}\n@keyframes hz-overview-ripple{0%{opacity:.85;transform:translate(-50%,-50%) scale(.14)}100%{opacity:0;transform:translate(-50%,-50%) scale(1.85)}}\n.hz-overview-weather{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-bottom:9px}\n.hz-overview-weather>div{background:#24567b60;border:1px solid #9cc9dc26;border-radius:8px;padding:7px 8px;min-width:0}\n.hz-overview-weather small{display:block;color:#98bfd5;font-size:clamp(8px,1vw,11px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-weather b{display:block;font-size:clamp(11px,1.6vw,17px);font-weight:550;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}\n.hz-overview-head{display:flex;align-items:center;justify-content:space-between;gap:6px;margin:0 2px 8px}\n.hz-overview-month{font-size:clamp(14px,1.8vw,18px);font-weight:600;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-buttons{display:flex;gap:5px;flex-shrink:0}\n.hz-overview button{border:1px solid #78afc463;background:#1b476688;color:#cdeeff;font:500 12px/1.2 inherit;\nborder-radius:8px;padding:6px 8px;min-height:30px;cursor:pointer}\n.hz-overview button:focus-visible{outline:2px solid #69eeee;outline-offset:2px}\n.hz-overview-weekdays,.hz-overview-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:3px}\n.hz-overview-weekdays{font-size:10px;letter-spacing:.05em;color:#83afc7;text-align:center;margin-bottom:4px}\n.hz-overview-days{flex:1;min-height:0;grid-template-rows:repeat(4,minmax(0,1fr))}\n.hz-overview-day{box-sizing:border-box;min-width:0;min-height:0;overflow:hidden;border:1px solid #81b7db25;\nborder-radius:6px;background:#122d467b;padding:4px 3px;display:flex;flex-direction:column;gap:3px}\n.hz-overview-day[data-today=\"1\"]{background:#16547cac;border-color:#74e5f0b0}\n.hz-overview-day[data-other=\"1\"]{color:#8faec6;background:#071c3166}\n.hz-overview-num{text-align:center;font-size:clamp(12px,1.7vw,18px);line-height:1.1}\n.hz-overview-day[data-today=\"1\"] .hz-overview-num{font-weight:700;color:#7ee8f2}\n.hz-overview-chip{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:clamp(8px,.95vw,11px);\nline-height:1.22;border-left:2px solid #47d9db;border-radius:2px;background:#1477a344;padding:2px 3px}\n.hz-overview-chip[data-all-day=\"1\"]{border-color:#b8b4ee;background:#746db244}\n.hz-overview-more{font-size:9px;color:#c6dce9}\n.hz-overview-foot{display:flex;align-items:center;gap:5px;margin-top:8px}\n.hz-overview-source{font-size:10px;color:#9cc0d3;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.hz-overview-config{position:absolute;inset:0;z-index:9;padding:18px;box-sizing:border-box;background:#081a30f8;\ndisplay:grid;align-content:center;gap:11px;overflow:auto}\n.hz-overview-config[hidden]{display:none!important}\n.hz-overview-config h3{font-size:17px;margin:0}\n.hz-overview-config label{display:grid;gap:5px;font-size:12px;color:#c9e3f1}\n.hz-overview-config input{box-sizing:border-box;width:100%;border:1px solid #7ebeda;background:#18364c;color:#fff;padding:9px;border-radius:7px;font:inherit}\n.hz-overview-config p{font-size:11px;color:#9bbacd;margin:0}\n.hz-overview-config-buttons{display:flex;justify-content:flex-end;gap:7px}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-info{z-index:15}\n@media(min-width:900px) and (orientation:landscape){.hz-overview{left:max(12px,calc((100% - 970px)/2));right:max(12px,calc((100% - 970px)/2));top:32vh}}\n@media(max-height:640px){.hz-overview{top:30vh;padding:6px 9px}.hz-overview-weather{margin-bottom:4px}\n.hz-overview-weather>div{padding:3px 6px}.hz-overview-day{padding:2px}.hz-overview-num{font-size:11px}.hz-overview-chip{font-size:8px}}\n@media(prefers-reduced-motion:reduce){.hz-ambient-head,.hz-ambient-stage,.hz-overview{transition:none!important}\n.hz-ambient-body[data-overview=\"open\"]::after{animation:none!important;display:none}}\n\n/* 0.4.76: Build the overview from the orb, like TAFA's traced information cards. */\n.hz-overview{isolation:isolate;box-shadow:0 23px 52px #030b1bd3,0 0 36px #39dfee18,inset 0 1px #aff6ff18}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview{\n animation:hz-overview-construct 1.15s cubic-bezier(.17,.78,.2,1) .2s both;\n transition:none;will-change:transform,opacity\n}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview{\n visibility:visible;pointer-events:none;animation:hz-overview-unbuild .69s cubic-bezier(.52,0,.8,.37) both;\n transition:none\n}\n@keyframes hz-overview-construct{\n 0%{opacity:0;filter:blur(5px);clip-path:inset(0 0 100% 0 round 17px);transform:translate3d(0,38px,0) scale(.97)}\n 17%{opacity:.93;filter:blur(0);clip-path:inset(0 0 95% 0 round 17px);transform:translate3d(0,28px,0) scale(.985)}\n 46%{opacity:1;clip-path:inset(0 0 48% 0 round 17px);transform:translate3d(0,13px,0) scale(.994)}\n 79%{opacity:1;clip-path:inset(0 0 6% 0 round 17px);transform:translate3d(0,2px,0) scale(.999)}\n 100%{opacity:1;filter:none;clip-path:inset(0 0 0 0 round 17px);transform:translate3d(0,0,0) scale(1)}\n}\n@keyframes hz-overview-unbuild{\n 0%{opacity:1;clip-path:inset(0 0 0 0 round 17px);transform:translate3d(0,0,0)}\n 48%{opacity:.9;clip-path:inset(0 0 45% 0 round 17px);transform:translate3d(0,15px,0)}\n 88%{opacity:.65;clip-path:inset(0 0 91% 0 round 17px);transform:translate3d(0,36px,0)}\n 100%{opacity:0;clip-path:inset(0 0 100% 0 round 17px);transform:translate3d(0,47px,0)}\n}\n/* An actual travelling light streak draws the panel border in four sections. */\n.hz-overview-edge{position:absolute;inset:0;z-index:8;pointer-events:none;border-radius:inherit}\n.hz-overview-edge i{position:absolute;display:block;background:#9ff7ffed;\n box-shadow:0 0 5px #b1f8ff,0 0 14px #58e8ff99,0 0 24px #31e6ee50}\n.hz-overview-edge .edge-n{left:16px;right:16px;top:0;height:1px;transform-origin:left}\n.hz-overview-edge .edge-e{right:0;top:16px;bottom:16px;width:1px;transform-origin:top}\n.hz-overview-edge .edge-s{bottom:0;right:16px;left:16px;height:1px;transform-origin:right}\n.hz-overview-edge .edge-w{left:0;top:16px;bottom:16px;width:1px;transform-origin:bottom}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-n{animation:hz-overview-trace-x .4s ease .42s both}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-e{animation:hz-overview-trace-y .33s ease .79s both}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-s{animation:hz-overview-trace-x .37s ease 1.08s both}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-w{animation:hz-overview-trace-y .3s ease 1.4s both}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-edge{opacity:0;transition:opacity .22s ease}\n@keyframes hz-overview-trace-x{from{opacity:0;transform:scaleX(0)}12%{opacity:1}to{opacity:.46;transform:scaleX(1)}}\n@keyframes hz-overview-trace-y{from{opacity:0;transform:scaleY(0)}12%{opacity:1}to{opacity:.46;transform:scaleY(1)}}\n.hz-overview-scan{position:absolute;inset:0;z-index:5;pointer-events:none;border-radius:inherit;\n background:linear-gradient(180deg,transparent 0%,#53e6fc00 44%,#8af8ff33 49%,#d3feff99 50%,#5dcdf933 51%,transparent 58%);\n opacity:0;transform:translate3d(0,-112%,0)}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-scan{animation:hz-overview-grid-scan 1.15s ease-out .43s both}\n@keyframes hz-overview-grid-scan{0%{opacity:0;transform:translate3d(0,-115%,0)}15%{opacity:1}75%{opacity:.6}100%{opacity:0;transform:translate3d(0,116%,0)}}\n/* Interior elements have separate arrival times instead of appearing as one finished rectangle. */\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div{animation:hz-overview-tile-rise .38s cubic-bezier(.2,.8,.2,1) both}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(1){animation-delay:.66s}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(2){animation-delay:.76s}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(3){animation-delay:.86s}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(4){animation-delay:.96s}\n.hz-overview[data-intro=\"1\"] .hz-overview-head{animation:hz-overview-tile-rise .37s ease .89s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-weekdays{animation:hz-overview-tile-rise .32s ease 1.02s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-day{animation:hz-overview-cell-in .31s cubic-bezier(.13,.79,.23,1.0) var(--hz-enter-delay,1.12s) both}\n.hz-overview[data-intro=\"1\"] .hz-overview-chip{animation:hz-overview-chip-in .3s ease var(--hz-event-delay,1.55s) both}\n.hz-overview[data-intro=\"1\"] .hz-overview-foot{animation:hz-overview-tile-rise .34s ease 1.61s both}\n@keyframes hz-overview-tile-rise{from{opacity:0;transform:translate3d(0,9px,0);filter:brightness(1.9)}to{opacity:1;transform:translate3d(0,0,0);filter:brightness(1)}}\n@keyframes hz-overview-cell-in{\n from{opacity:0;transform:translate3d(0,11px,0) scale(.97);border-color:#aef9ffb8}\n 62%{opacity:1;transform:translate3d(0,0,0) scale(1);border-color:#79e2ee88}\n to{opacity:1;transform:translate3d(0,0,0) scale(1)}\n}\n@keyframes hz-overview-chip-in{from{opacity:0;clip-path:inset(0 100% 0 0)}25%{opacity:1}to{opacity:1;clip-path:inset(0 0 0 0)}}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-weather,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-head,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-weekdays,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-days,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-foot{animation:hz-overview-content-out .24s ease both}\n@keyframes hz-overview-content-out{from{opacity:1;transform:translateY(0)}to{opacity:0;transform:translateY(-8px)}}\n.hz-overview-beam{position:absolute;inset:0;width:100%;height:100%;z-index:7;pointer-events:none;\n overflow:visible;opacity:0;will-change:opacity}\n.hz-overview-beam path{fill:none;stroke:#73f4ff;stroke-width:1.6;\n filter:drop-shadow(0 0 5px #73f8ff);stroke-linecap:round}\n.hz-overview-beam circle{fill:#defbff;filter:drop-shadow(0 0 8px #5ce8fe)}\n.hz-overview-bloom{position:absolute;z-index:4;left:50%;top:29%;width:180px;height:180px;\n border-radius:50%;pointer-events:none;opacity:0;transform:translate(-50%,-50%) scale(.25);\n background:radial-gradient(circle,#61faee4d 0%,#28f1e92b 23%,#0b9e9e00 66%);\n box-shadow:0 0 0 1px #86faff50,0 0 40px #55f5e638}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-bloom{\n animation:hz-overview-bloom 1.05s cubic-bezier(.14,.9,.23,1) both}\n@keyframes hz-overview-bloom{\n 0%{opacity:0;transform:translate(-50%,-50%) scale(.18)}\n 20%{opacity:.85}\n 66%{opacity:.55;transform:translate(-50%,-50%) scale(2)}\n 100%{opacity:0;transform:translate(-50%,-50%) scale(2.7)}\n}\n/* Reduced motion still gives an instantly usable family calendar. */\n@media(prefers-reduced-motion:reduce){\n .hz-ambient-body[data-overview=\"open\"] .hz-overview,\n .hz-ambient-body[data-overview=\"closing\"] .hz-overview,\n .hz-overview[data-intro=\"1\"] .hz-overview-weather>div,\n .hz-overview[data-intro=\"1\"] .hz-overview-head,\n .hz-overview[data-intro=\"1\"] .hz-overview-weekdays,\n .hz-overview[data-intro=\"1\"] .hz-overview-day,\n .hz-overview[data-intro=\"1\"] .hz-overview-chip,\n .hz-overview[data-intro=\"1\"] .hz-overview-foot,\n .hz-ambient-body[data-overview=\"open\"] .hz-overview-edge i,\n .hz-ambient-body[data-overview=\"open\"] .hz-overview-bloom,\n .hz-ambient-body[data-overview=\"open\"] .hz-overview-scan{animation:none!important}\n .hz-ambient-body[data-overview=\"open\"] .hz-overview{opacity:1;clip-path:none;transform:none;visibility:visible}\n .hz-overview-edge,.hz-overview-beam,.hz-overview-bloom,.hz-overview-scan{display:none!important}\n}\n\n/* Moving shooting-stars, grid illumination and node hits from the reference transition. */\n.hz-overview-particles{position:absolute;inset:0;width:100%;height:100%;z-index:11;\npointer-events:none;opacity:0;contain:layout paint}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-particles{opacity:1}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-particles{opacity:1}\n@media(prefers-reduced-motion:reduce){.hz-overview-particles{display:none!important}}\n\n/* TAFA ambient overview v0.4.80: reference-proportion portrait composition.\n   Keep all changes restricted to an already-open overview. */\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-head,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-head {\n position:absolute!important;top:clamp(10px,2vh,23px)!important;left:clamp(14px,3vw,28px)!important;\n margin:0!important;text-align:left!important;transform:none!important;z-index:8\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-time,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-time{\n font-size:clamp(48px,9vw,86px)!important;line-height:1;letter-spacing:-.055em\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-date,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-date{\n margin-top:6px!important;font-size:clamp(11px,1.5vw,15px)!important\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-stage,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-stage{\n position:absolute!important;top:clamp(85px,11vh,145px)!important;left:50%!important;right:auto!important;\n width:min(98%,640px)!important;height:clamp(195px,26vh,330px)!important;max-height:none!important;\n min-height:0!important;flex:none!important;margin:0!important;\n transform:translate3d(-50%,0,0) scale(.94)!important;transform-origin:50% 48%!important;\n opacity:.96!important;z-index:2\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-metric b,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-metric b{font-size:clamp(9px,1.15vw,13px)!important}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-metric small,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-metric small{font-size:8px!important}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-foot{opacity:0!important}\n.hz-overview{\n left:clamp(6px,1.6vw,16px)!important;right:clamp(6px,1.6vw,16px)!important;bottom:clamp(8px,1vh,16px)!important;\n border-radius:12px!important;padding:7px 10px 7px!important;\n background:linear-gradient(180deg,#13334ee3 0%,#0a1d35e8 36%,#071b31ec 100%)!important;\n border:1px solid #7edafa57!important;\n box-shadow:0 14px 40px #010817a6,inset 0 1px #b5f7ff32!important\n}\n.hz-ambient-body[data-tablet=\"0\"][data-overview=\"open\"] .hz-ambient-stage,\n.hz-ambient-body[data-tablet=\"0\"][data-overview=\"closing\"] .hz-ambient-stage{\n height:clamp(185px,23vh,310px)!important}\n.hz-ambient-body[data-tablet=\"0\"] .hz-overview{top:clamp(280px,34vh,370px)!important}\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview{top:clamp(285px,37vh,430px)!important}\n.hz-overview-forecast{display:grid;grid-template-columns:1.45fr repeat(5,minmax(0,1fr));gap:0;\n border:1px solid #7fc3e343;border-radius:9px;overflow:hidden;background:#173b5eb0;\n min-height:60px;margin:0 0 5px}\n.hz-overview-today{display:flex;align-items:center;gap:6px;min-width:0;padding:6px 7px;\n background:linear-gradient(110deg,#305b85aa,#19416488);border-right:1px solid #9de2ff3d}\n.hz-overview-today-icon{font-size:clamp(23px,3.7vw,33px);line-height:1;filter:drop-shadow(0 1px 4px #b7edff66)}\n.hz-overview-today-main{display:grid;gap:2px;min-width:0}\n.hz-overview-today-day{font-size:8px;letter-spacing:.09em;font-weight:700;color:#d8edfb;white-space:nowrap}\n.hz-overview-today-temp{font-size:clamp(17px,2.8vw,25px);line-height:1.1;font-weight:600;white-space:nowrap}\n.hz-overview-today-desc{font-size:9px;color:#a7c8de;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-forecast-item{min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;\n gap:3px;padding:5px 2px;color:#c1daeb;text-align:center}\n.hz-overview-forecast-item+.hz-overview-forecast-item{border-left:1px solid #82b8e71c}\n.hz-overview-forecast-item small{font-size:9px;letter-spacing:.06em;color:#c6dfec}\n.hz-overview-forecast-icon{font-size:clamp(14px,2.1vw,19px);line-height:1}\n.hz-overview-forecast-temps{font-size:clamp(9px,1.2vw,13px);font-weight:550;white-space:nowrap;color:#ecf7ff}\n.hz-overview-forecast-temps em{font-style:normal;font-size:9px;opacity:.68}\n.hz-overview-energy{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));min-height:34px;\n border:1px solid #579ac53b;border-radius:7px;background:#0e2b485c;overflow:hidden;\n margin-bottom:clamp(6px,1vh,12px)}\n.hz-overview-energy>div{min-width:0;padding:5px 7px;border-right:1px solid #89c2e727}\n.hz-overview-energy>div:last-child{border-right:0}\n.hz-overview-energy small{display:block;font-size:8px;color:#83bad1;letter-spacing:.07em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-energy b{display:block;font-size:clamp(10px,1.35vw,13px);font-weight:600;color:#e7f6ff;\n overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.hz-overview-head{margin:0 2px 5px!important;min-height:25px}\n.hz-overview-month{font-size:clamp(11px,1.5vw,15px)!important;font-weight:550!important;color:#eaf5ff}\n.hz-overview-buttons button{min-height:26px!important;padding:4px 6px!important}\n.hz-overview-weekdays{font-size:9px!important;color:#8caec3!important;margin-bottom:2px!important;gap:2px}\n.hz-overview-days{gap:1px!important;grid-template-rows:repeat(4,minmax(0,1fr))!important}\n.hz-overview-day{border:1px solid transparent!important;border-radius:3px!important;background:transparent!important;\n padding:3px 1px!important;gap:3px!important;transition:background-color .75s ease,border-color .75s ease}\n.hz-overview[data-intro=\"1\"] .hz-overview-day{background:#14416029!important;border-color:#84ddec40!important}\n.hz-overview[data-intro=\"0\"] .hz-overview-day{background:transparent!important;border-color:transparent!important}\n.hz-overview-day[data-today=\"1\"]{background:#15547666!important;border-color:#49d9ec66!important}\n.hz-overview-day[data-today=\"1\"] .hz-overview-num{color:#7ae8f5!important}\n.hz-overview-day[data-today=\"1\"][data-intro=\"0\"]{background:#164e7777!important;border-color:#4fe7ec5c!important}\n.hz-overview-num{font-size:clamp(13px,1.9vw,23px)!important;line-height:1.08!important;font-weight:400!important}\n.hz-overview-chip{background:#138caf53!important;border-left:2px solid #3ce6ed!important;\n color:#e3f8ff!important;border-radius:2px!important;font-size:clamp(8px,1.08vw,12px)!important;\n line-height:1.18!important;padding:2px 3px!important}\n.hz-overview-chip[data-all-day=\"1\"]{background:#38699488!important;border-color:#98def5!important}\n.hz-overview-foot{margin-top:5px!important;min-height:26px}\n.hz-overview-source{font-size:9px!important;opacity:.7}\n.hz-overview-foot button{font-size:10px!important;padding:3px 6px!important;min-height:25px!important}\n.hz-overview-bottom{display:flex;align-items:center;gap:8px;min-height:33px;\n padding:4px 8px;border-radius:8px;border:1px solid #79c1e44a;\n background:#0d2d4aaf;margin-top:5px;color:#c0dded}\n.hz-overview-bottom-label{font-size:9px;color:#70cfe3;letter-spacing:.12em;font-weight:600;white-space:nowrap}\n.hz-overview-bottom-text{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;color:#d9eeff;min-width:0}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast{animation:hz-overview-tile-rise .4s ease .57s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-energy{animation:hz-overview-tile-rise .4s ease .86s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-bottom{animation:hz-overview-tile-rise .4s ease 1.65s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast-item{animation:hz-overview-tile-rise .28s ease both}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast-item:nth-child(2){animation-delay:.7s}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast-item:nth-child(3){animation-delay:.78s}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast-item:nth-child(4){animation-delay:.86s}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast-item:nth-child(5){animation-delay:.94s}\n.hz-overview[data-intro=\"1\"] .hz-overview-forecast-item:nth-child(6){animation-delay:1.02s}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge i{transition:opacity .3s ease}\n@media(max-height:650px){.hz-overview{padding:5px 7px!important}\n .hz-overview-forecast{min-height:45px}\n .hz-overview-energy{min-height:27px}\n .hz-overview-energy>div{padding:2px 4px}\n .hz-overview-bottom{min-height:24px}\n .hz-overview-num{font-size:12px!important}\n}\n@media(prefers-reduced-motion:reduce){.hz-overview[data-intro=\"1\"] .hz-overview-forecast,\n .hz-overview[data-intro=\"1\"] .hz-overview-energy,\n .hz-overview[data-intro=\"1\"] .hz-overview-forecast-item,\n .hz-overview[data-intro=\"1\"] .hz-overview-bottom{animation:none!important}}\n\n/* TAFA v0.4.83 — reference-style transparent calendar and stable Sphere transition.\n * Do not move/reflow the live Sphere element while scaling it. The 3D sphere\n * continues rendering and the native Assist stream remains untouched. */\n.hz-ambient-body[data-tablet] .hz-ambient-stage{\n  transition:transform 1120ms cubic-bezier(.18,.82,.22,1),\n    opacity 850ms ease!important;\n  backface-visibility:hidden;\n  will-change:transform\n}\n.hz-ambient-body[data-tablet][data-overview=\"open\"] .hz-ambient-stage,\n.hz-ambient-body[data-tablet][data-overview=\"closing\"] .hz-ambient-stage{\n  position:relative!important;\n  top:auto!important;left:auto!important;right:auto!important;\n  margin:clamp(0px,2vh,20px) auto 14px!important;\n  flex:1 0 auto!important;\n  width:min(100%,750px)!important;max-width:750px!important;\n  min-height:280px!important;max-height:62dvh!important;\n  height:clamp(280px,50dvh,590px)!important;\n  opacity:1!important;\n  transform-origin:50% 43%!important;\n  transition:transform 1120ms cubic-bezier(.18,.82,.22,1),\n    opacity 850ms ease!important\n}\n.hz-ambient-body[data-tablet=\"1\"][data-overview=\"open\"] .hz-ambient-stage,\n.hz-ambient-body[data-tablet=\"1\"][data-overview=\"closing\"] .hz-ambient-stage{\n  width:100%!important;max-width:680px!important;\n  height:48vh!important;min-height:180px!important;max-height:60vh!important;\n  flex:1 1 auto!important\n}\n.hz-ambient-body[data-tablet][data-overview=\"open\"] .hz-ambient-stage{\n  transform:translate3d(var(--hz-sphere-dx,0px),var(--hz-sphere-dy,-11vh),0)\n    scale(var(--hz-sphere-scale,.48))!important\n}\n.hz-ambient-body[data-tablet][data-overview=\"closing\"] .hz-ambient-stage{\n  transform:translate3d(0,0,0) scale(1)!important\n}\n/* An open overview has no permanent frosted rectangle over the calendar.\n   Independent forecast, energy and footer elements keep their own surfaces. */\n.hz-overview{\n  background:transparent!important;border-color:transparent!important;\n  box-shadow:none!important;\n  backdrop-filter:none!important;-webkit-backdrop-filter:none!important;\n  isolation:isolate;\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview{\n  animation-name:hz-overview-soft-in;\n  animation-duration:1050ms;\n  animation-timing-function:cubic-bezier(.18,.82,.22,1);\n  animation-fill-mode:both;\n  animation-delay:100ms;\n  clip-path:none!important;\n  filter:none!important\n}\n@keyframes hz-overview-soft-in{\n  0%{opacity:0;transform:translate3d(0,15px,0) scale(.995)}\n  35%{opacity:.45}\n  100%{opacity:1;transform:translate3d(0,0,0) scale(1)}\n}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview{\n  animation-name:hz-overview-soft-out;\n  animation-duration:670ms;animation-delay:0s\n}\n@keyframes hz-overview-soft-out{\n  from{opacity:1;transform:translate3d(0,0,0)}\n  to{opacity:0;transform:translate3d(0,12px,0)}\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-edge{\n  animation:hz-overview-edge-expire 2000ms ease both\n}\n@keyframes hz-overview-edge-expire{\n  0%{opacity:0}18%{opacity:1}68%{opacity:1}100%{opacity:0}\n}\n.hz-overview-days{\n  column-gap:clamp(2px,.7vw,8px)!important;row-gap:0!important;\n  grid-template-rows:repeat(4,minmax(0,1fr))!important\n}\n.hz-overview-day,\n.hz-overview[data-intro=\"0\"] .hz-overview-day,\n.hz-overview[data-intro=\"1\"] .hz-overview-day{\n  position:relative;\n  border:0!important;border-color:transparent!important;\n  border-radius:0!important;background:transparent!important;\n  box-shadow:none!important;overflow:hidden;\n  padding:clamp(3px,.65vh,7px) 2px!important;\n  align-items:stretch;\n  gap:clamp(3px,.5vh,6px)!important;\n}\n.hz-overview-num{\n  color:#dceaf7!important;\n  text-align:center;\n  font-size:clamp(21px,3.5vw,34px)!important;\n  font-weight:350!important;\n  letter-spacing:-.042em;\n  line-height:1.15!important;\n  font-variant-numeric:tabular-nums\n}\n.hz-overview-day[data-other=\"1\"] .hz-overview-num{opacity:.65}\n.hz-overview-day[data-today=\"1\"],\n.hz-overview[data-intro=\"0\"] .hz-overview-day[data-today=\"1\"]{\n  background:transparent!important;border:0!important\n}\n.hz-overview-day[data-today=\"1\"] .hz-overview-num{\n  display:flex;align-items:center;justify-content:center;\n  width:clamp(31px,4.4vw,43px);height:clamp(31px,4.4vw,43px);\n  margin:0 auto;\n  color:#d8fcff!important;font-weight:650!important;\n  background:radial-gradient(circle at 40% 28%,#25c8e9b5,#13779dbf 74%);\n  border-radius:50%;box-shadow:0 0 21px #28c3e965,0 0 0 1px #5ee4f277\n}\n.hz-overview-monthmark{\n  position:absolute;left:4px;top:1px;font-size:clamp(10px,1.25vw,14px);\n  color:#a9d9ed;font-weight:550;letter-spacing:.025em;\n  pointer-events:none\n}\n.hz-overview-day[data-month-start=\"1\"] .hz-overview-num{padding-top:8px}\n.hz-overview-chip,.hz-overview-chip[data-all-day=\"1\"]{\n  margin:0 1px;max-width:calc(100% - 2px);\n  background:#089fc488!important;border:0!important;\n  border-radius:2px!important;color:#dffaff!important;\n  padding:2px 4px!important;font-size:clamp(8px,1.12vw,11px)!important;\n  font-weight:480;letter-spacing:0;\n  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;\n  box-shadow:inset 0 1px #85eeff26\n}\n.hz-overview-chip[data-all-day=\"1\"]{background:#129eb78e!important}\n.hz-overview-weekdays{font-size:clamp(9px,1.2vw,12px)!important}\n.hz-overview-scan{pointer-events:none}\n@media(max-height:650px){\n .hz-overview-num{font-size:clamp(18px,2.8vw,26px)!important}\n .hz-overview-day[data-today=\"1\"] .hz-overview-num{height:30px;width:30px}\n .hz-overview-chip{font-size:8px!important}\n}\n@media(prefers-reduced-motion:reduce){\n .hz-ambient-body[data-tablet][data-overview=\"open\"] .hz-ambient-stage{\n    transition:none!important;transform:translate3d(var(--hz-sphere-dx,0px),var(--hz-sphere-dy,-11vh),0)\n    scale(var(--hz-sphere-scale,.48))!important\n }\n .hz-ambient-body[data-tablet][data-overview=\"closing\"] .hz-ambient-stage{\n    transition:none!important;transform:none!important\n }\n .hz-ambient-body[data-overview=\"open\"] .hz-overview,\n .hz-ambient-body[data-overview=\"closing\"] .hz-overview{\n    animation:none!important;opacity:1;transform:none\n }\n}\n\n/* 0.4.84: preserve header's flow height. Making the clock absolute caused\n   the stage to shift upward AFTER its pre-animation destination was measured. */\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-head,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-head{\n position:relative!important;top:auto!important;left:auto!important;\n right:auto!important;bottom:auto!important;width:100%!important;\n max-width:100%!important;box-sizing:border-box!important;\n margin-top:clamp(52px,8vh,96px)!important;margin-bottom:0!important;\n padding-left:clamp(10px,2vw,20px)!important;\n text-align:left!important;transform:none!important;\n flex-shrink:0!important\n}\n/* Preserve the same layout geometry on the Android tablet as in its\n   ordinary ambient view. Only horizontal text alignment changes. */\n.hz-ambient-body[data-tablet=\"1\"][data-overview=\"open\"] .hz-ambient-head,\n.hz-ambient-body[data-tablet=\"1\"][data-overview=\"closing\"] .hz-ambient-head{\n margin-top:clamp(48px,9vh,80px)!important\n}\n.hz-ambient-body[data-tablet][data-overview=\"open\"] .hz-ambient-stage,\n.hz-ambient-body[data-tablet][data-overview=\"closing\"] .hz-ambient-stage{\n transform-origin:50% 50%!important\n}\n\n/* Match the resting clock's dimensions to avoid even a small vertical\n   reflow when switching views. Only its horizontal alignment changes. */\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-time,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-time{\n font-size:clamp(62px,10.4vw,116px)!important;line-height:1.04!important\n}\n.hz-ambient-body[data-tablet=\"1\"][data-overview=\"open\"] .hz-ambient-time,\n.hz-ambient-body[data-tablet=\"1\"][data-overview=\"closing\"] .hz-ambient-time{\n font-size:clamp(56px,10vw,90px)!important\n}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-date,\n.hz-ambient-body[data-overview=\"closing\"] .hz-ambient-date{\n font-size:clamp(13px,1.55vw,17px)!important;margin-top:8px!important\n}\n\n/* Annäherung und Schließmodus – lokal pro Tablet, ohne feste Mindestzeit. */\n.hz-overview-config select{\n  box-sizing:border-box;width:100%;border:1px solid #7ebeda;\n  background:#18364c;color:#fff;padding:9px;border-radius:7px;\n  font:inherit;min-height:39px\n}\n.hz-overview-config [data-presence-current]{\n  color:#8ee4ed;font-size:11px;overflow-wrap:anywhere\n}\n\n/* 0.4.86: T590/Android compositing profile, only during calendar view.\n * One opacity animation for the grid instead of 28 concurrent filters,\n * masks and clip paths. Desktop keeps the full choreographed effects. */\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-days{\n animation:hz-overview-lite-reveal .52s cubic-bezier(.19,.82,.25,1) .46s both!important\n}\n@keyframes hz-overview-lite-reveal{\n from{opacity:0;transform:translate3d(0,6px,0)}\n to{opacity:1;transform:translate3d(0,0,0)}\n}\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-day,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-chip,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-weekdays,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-weather>div,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-forecast-item,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-forecast,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-energy,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-head,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-foot,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-bottom{\n animation:none!important;filter:none!important;clip-path:none!important\n}\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview-edge,\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview-scan{\n display:none!important\n}\n.hz-ambient-body[data-tablet=\"1\"] .hz-overview-bloom{\n filter:none!important;box-shadow:none!important\n}\n@media(prefers-reduced-motion:reduce){\n .hz-ambient-body[data-tablet=\"1\"] .hz-overview[data-intro=\"1\"] .hz-overview-days{\n   animation:none!important;opacity:1!important;transform:none!important\n }\n}\n";
export function mountOverview(card,s){
  if(s.overview||!s.host)return;
  const host=s.host,style=document.createElement("style");style.textContent=CSS;host.append(style);
  const panel=document.createElement("section");panel.className="hz-overview";
  panel.setAttribute("aria-label","Familienkalender und Hausübersicht");panel.setAttribute("aria-hidden","true");
  panel.innerHTML=`
  <div class="hz-overview-forecast" aria-label="Wettervorhersage">
    <div class="hz-overview-today"><span class="hz-overview-today-icon" data-today-icon>☁️</span>
      <div class="hz-overview-today-main"><span class="hz-overview-today-day" data-today-label>HEUTE</span>
      <strong class="hz-overview-today-temp" data-today-temp>—</strong>
      <span class="hz-overview-today-desc" data-today-desc>Wetter</span></div></div>
    <div class="hz-overview-forecast-item" data-forecast-day="1"><small>—</small><span class="hz-overview-forecast-icon">·</span><span class="hz-overview-forecast-temps">—</span></div>
    <div class="hz-overview-forecast-item" data-forecast-day="2"><small>—</small><span class="hz-overview-forecast-icon">·</span><span class="hz-overview-forecast-temps">—</span></div>
    <div class="hz-overview-forecast-item" data-forecast-day="3"><small>—</small><span class="hz-overview-forecast-icon">·</span><span class="hz-overview-forecast-temps">—</span></div>
    <div class="hz-overview-forecast-item" data-forecast-day="4"><small>—</small><span class="hz-overview-forecast-icon">·</span><span class="hz-overview-forecast-temps">—</span></div>
    <div class="hz-overview-forecast-item" data-forecast-day="5"><small>—</small><span class="hz-overview-forecast-icon">·</span><span class="hz-overview-forecast-temps">—</span></div>
  </div>
  <div class="hz-overview-energy" aria-label="Hauswerte">
    <div><small>SOLAR</small><b data-oe="solar">—</b></div>
    <div><small>NETZ</small><b data-oe="grid">—</b></div>
    <div><small>STROMPREIS</small><b data-oe="price">—</b></div>
    <div><small>AUẞEN</small><b data-oe="outside">—</b></div>
  </div>
  <div class="hz-overview-head"><span class="hz-overview-month">Familienkalender</span>
   <div class="hz-overview-buttons"><button type="button" data-oa="prev" aria-label="Vorherige vier Wochen">‹</button>
   <button type="button" data-oa="today">Heute</button><button type="button" data-oa="next" aria-label="Nächste vier Wochen">›</button></div></div>
  <div class="hz-overview-weekdays" aria-hidden="true"><span>SO</span><span>MO</span><span>DI</span><span>MI</span><span>DO</span><span>FR</span><span>SA</span></div>
  <div class="hz-overview-days" role="grid" aria-label="Kalender für vier Wochen"></div>
  <div class="hz-overview-bottom" aria-label="Nächster Familientermin"><span class="hz-overview-bottom-label">FAMILIE</span>
    <span class="hz-overview-bottom-text" data-next-event>Termine werden geladen …</span></div>
  <div class="hz-overview-foot"><span class="hz-overview-source">Kalender wird geprüft …</span>
  <button type="button" data-oa="config" aria-label="Kalender einstellen">⚙</button>
  <button type="button" data-oa="close">Zur Kugel</button></div>
  <div class="hz-overview-config" hidden><h3>Familienübersicht</h3>
    <label>Familienkalender in Home Assistant (leer = automatisch)
      <input data-setting="calendar" placeholder="calendar.familie" autocomplete="off"></label>
    <label>Annäherungssensor (leer = eigenes Tablet automatisch)
      <input data-setting="presence" placeholder="Automatisch nach TAFA-Gerätename" autocomplete="off"></label>
    <p data-presence-current>Gerätesensor wird geprüft …</p>
    <label>Übersicht schließen
      <select data-setting="dismiss">
        <option value="sensor">Sofort, sobald Annäherung „Frei“ meldet</option>
        <option value="time">Nach eingestellter Zeit</option>
        <option value="either">Bei „Frei“ oder nach Zeit (was zuerst passiert)</option>
      </select></label>
    <label>Anzeigedauer in Sekunden (0 = keine Zeitbegrenzung)
      <input data-setting="idle" type="number" min="0" step="any" inputmode="decimal"></label>
    <p>Jedes Tablet verwendet ausschließlich seinen eigenen Annäherungssensor. Bei manuellem Öffnen ohne erkannte Annäherung gilt die eingestellte Zeit als Rückfall. 0 deaktiviert nur den Timer, nicht das Schließen bei „Frei“.</p>
    <div class="hz-overview-config-buttons"><button type="button" data-oa="cancel">Abbrechen</button>
      <button type="button" data-oa="save">Speichern</button></div></div>`;
  // Visual trace elements are independent of HA events and Android audio.
  const edge=document.createElement("div");
  edge.className="hz-overview-edge";edge.setAttribute("aria-hidden","true");
  edge.innerHTML='<i class="edge-n"></i><i class="edge-e"></i><i class="edge-s"></i><i class="edge-w"></i>';
  const scan=document.createElement("div");
  scan.className="hz-overview-scan";scan.setAttribute("aria-hidden","true");
  panel.append(edge,scan);
  const bloom=document.createElement("div");bloom.className="hz-overview-bloom";bloom.setAttribute("aria-hidden","true");
  const SVGNS="http://www.w3.org/2000/svg";
  const beam=document.createElementNS(SVGNS,"svg");beam.setAttribute("class","hz-overview-beam");
  beam.setAttribute("aria-hidden","true");
  const ray=document.createElementNS(SVGNS,"path");
  const spark=document.createElementNS(SVGNS,"circle");
  spark.setAttribute("r","3.25");beam.append(ray,spark);
  const particles=document.createElement("canvas");
  particles.className="hz-overview-particles";
  particles.setAttribute("aria-hidden","true");
  host.append(bloom,beam,panel,particles);
  const STORE="tafa.ambient.overview.v1";
  let cfg={calendar:"",presence:"",dismiss:"sensor",idle:55},
    monthOffset=0,events=[],requestedCalendar="",lastFetch=0;
  let ongoing=false,serial=0,opened=false,disposed=false,wasPresent=false,
    boundPresenceId="",openedBySensor=false,lastTouch=0,lastWeather=0;
  let lastCalendarFingerprint="";
  let forecastData=[],forecastAt=0,forecastPending=false,forecastSerial=0;
  let revealTimer=null,collapseTimer=null,beamFrame=null,beamToken=0;
  try{
    const obj=JSON.parse(localStorage.getItem(STORE)||"{}");
    if(obj&&typeof obj==="object"){
      if(typeof obj.calendar==="string"&&/^calendar\.[a-z0-9_]+$/.test(obj.calendar))cfg.calendar=obj.calendar;
      if(typeof obj.presence==="string"&&/^(sensor|binary_sensor)\.[a-z0-9_]+$/.test(obj.presence))cfg.presence=obj.presence;
      if(typeof obj.dismiss==="string"&&["sensor","time","either"].includes(obj.dismiss))
        cfg.dismiss=obj.dismiss;
      if(obj.idle!==undefined&&Number.isFinite(Number(obj.idle))&&Number(obj.idle)>=0)
        cfg.idle=Number(obj.idle);
    }
  }catch{}
  const q=selector=>panel.querySelector(selector);
  const setStatus=text=>{q(".hz-overview-source").textContent=String(text||"");};
  const slug=value=>String(value||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"")
    .toLowerCase().replace(/ß/g,"ss").replace(/[^a-z0-9]+/g,"_")
    .replace(/^_+|_+$/g,"");
  const resolvePresenceId=states=>{
    // Explicit per-display selection always wins. Automatic resolution only
    // works on a dashboard bound to an actual TAFA tablet/voice sensor.
    if(cfg.presence)return states[cfg.presence]?cfg.presence:"";
    const voice=card._tafaLocalVoice;
    if(!voice?.status||!states[voice.status])return "";
    const friendly=String(states[voice.status]?.attributes?.friendly_name||"");
    const nameFromStatus=friendly.replace(/^TAFA\s*[·:-]\s*/i,"")
      .replace(/\s*Rufwortstatus\s*$/i,"").trim();
    const names=[voice.label,voice.room,nameFromStatus].filter(Boolean);
    const roomSlugs=[...new Set(names.map(slug).filter(Boolean))];
    for(const room of roomSlugs){
      for(const suffix of ["annaherung","annaeherung"]){
        const id="binary_sensor.tafa_"+room+"_"+suffix;
        if(states[id])return id;
      }
    }
    // Stable, non-ID match for installations where the entity ID was
    // customized in HA. Require exactly one matching device display name.
    const candidates=Object.keys(states).filter(id=>
      id.startsWith("binary_sensor.")&&
      /annäherung|annaeherung|annaherung/i.test(
        String(states[id]?.attributes?.friendly_name||"")+" "+id)&&
      names.some(name=>{
        const n=slug(name);
        const label=slug(String(states[id]?.attributes?.friendly_name||"")
          .replace(/^TAFA\s*[·:-]\s*/i,"").replace(/\s*Annäherung\s*$/i,""));
        return n&&n===label;
      })
    );
    return candidates.length===1?candidates[0]:"";
  };
  const calendarId=()=>{
    const states=card.h?.states||{};
    if(cfg.calendar)return states[cfg.calendar]?cfg.calendar:"";
    const ids=Object.keys(states).filter(id=>id.startsWith("calendar."));
    return ids.find(id=>/^calendar\.(familie|family)(?:_|$)/i.test(id))||
      ids.find(id=>/\bfamilie\b|\bfamily\b/i.test(states[id]?.attributes?.friendly_name||""))||"";
  };
  const localDay=()=>{const d=new Date();d.setHours(0,0,0,0);
    d.setDate(d.getDate()-d.getDay()+monthOffset*28);return d;};
  const add=(date,count)=>{const v=new Date(date);v.setDate(v.getDate()+count);return v;};
  const key=d=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-");
  const eventDate=obj=>{
    const str=typeof obj==="string"?obj:(obj?.dateTime||obj?.date||"");
    if(!str)return null;
    const normalized=/^\d{4}-\d\d-\d\d$/.test(str)?str+"T12:00:00":
      String(str).replace(/^(\d{4}-\d\d-\d\d)\s+(\d\d:\d\d)/,"$1T$2");
    const d=new Date(normalized);
    return Number.isNaN(d.getTime())?null:d;
  };
  const draw=()=>{
    if(!opened||disposed)return;
    const start=localDay(),end=add(start,27);
    // A calendar service response can arrive with the *same* records as
    // the entity-state fallback. Avoid tearing down and rebuilding all
    // 28 calendar DOM cells a second/third time during the intro.
    const fingerprint=key(start)+"|"+key(new Date())+"|"+
      events.map(e=>[typeof e.start==="string"?e.start:JSON.stringify(e.start),
        typeof e.end==="string"?e.end:JSON.stringify(e.end),e.summary||e.title||""].join("~")).join(";");
    if(fingerprint===lastCalendarFingerprint)return;
    lastCalendarFingerprint=fingerprint;
    const fmt=d=>d.toLocaleDateString("de-DE",{month:"long",year:"numeric"});
    q(".hz-overview-month").textContent=fmt(start)===fmt(end)?fmt(start):fmt(start)+" – "+fmt(end);
    const grouped=new Map();
    for(const item of events.slice(0,300)){
      const a=eventDate(item.start),b=eventDate(item.end);
      if(!a||!b||b<=a)continue;
      const allDay=typeof item.start==="string"&&/^\d{4}-\d\d-\d\d$/.test(item.start);
      const from=new Date(a);from.setHours(0,0,0,0);
      const until=new Date(b);until.setHours(0,0,0,0);
      if(!allDay&&b>until)until.setDate(until.getDate()+1);
      for(let d=from,c=0;d<until&&c<32;d=add(d,1),c++){
        if(d<start||d>=add(start,28))continue;
        const k=key(d);if(!grouped.has(k))grouped.set(k,[]);
        grouped.get(k).push({title:String(item.summary||"Termin").slice(0,120),allDay,start:a});
      }
    }
    const grid=q(".hz-overview-days");grid.replaceChildren();
    const today=key(new Date());
    for(let i=0;i<28;i++){
      const day=add(start,i),k=key(day),items=(grouped.get(k)||[]).sort((a,b)=>a.start-b.start);
      const cell=document.createElement("div");cell.className="hz-overview-day";cell.setAttribute("role","gridcell");
      cell.dataset.today=k===today?"1":"0";cell.dataset.other=day.getMonth()===start.getMonth()?"0":"1";
      cell.style.setProperty("--hz-enter-delay",String(1030+Math.floor(i/7)*125+(i%7)*25)+"ms");
      cell.style.setProperty("--hz-event-delay",String(1360+Math.floor(i/7)*125+(i%7)*25)+"ms");
      cell.setAttribute("aria-label",day.toLocaleDateString("de-DE",{weekday:"long",day:"numeric",month:"long"}));
      const num=document.createElement("span");
      num.className="hz-overview-num";
      num.textContent=String(day.getDate());
      cell.dataset.monthStart=day.getDate()===1?"1":"0";
      cell.append(num);
      if(day.getDate()===1){
        const mark=document.createElement("span");
        mark.className="hz-overview-monthmark";
        mark.setAttribute("aria-hidden","true");
        mark.textContent=day.toLocaleDateString("de-DE",{month:"short"}).replace(/\.$/,"");
        cell.append(mark);
      }
      for(const item of items.slice(0,2)){
        const chip=document.createElement("span");chip.className="hz-overview-chip";chip.dataset.allDay=item.allDay?"1":"0";
        chip.textContent=item.title;chip.title=item.title;cell.append(chip);
      }
      if(items.length>2){const more=document.createElement("span");more.className="hz-overview-more";more.textContent="+"+(items.length-2)+" weitere";cell.append(more);}
      grid.append(cell);
    }
    // The reference's bottom strip shows contextual information. Do not
    // fabricate a news headline when no news feed is configured.
    const next=events.filter(e=>{
      const until=eventDate(e.end);
      const startOfDay=new Date();startOfDay.setHours(0,0,0,0);
      return until&&until>=startOfDay;
    }).sort((a,b)=>(eventDate(a.start)||0)-(eventDate(b.start)||0))[0];
    const teaser=q("[data-next-event]");
    if(teaser){
      if(next){
        const day=eventDate(next.start);
        const today=new Date().toDateString();
        const label=day?.toDateString()===today?"Heute":
          day?.toLocaleDateString("de-DE",{weekday:"short",day:"numeric",month:"short"})||"";
        teaser.textContent=label+" · "+String(next.summary||"Familientermin");
      }else teaser.textContent="Keine weiteren Termine in den angezeigten Wochen";
    }
  };
  // The calendar entity already publishes the current event as state
  // attributes. Render it immediately, even if the room browser cannot call
  // a calendar service. This keeps an all-day test appointment visible.
  const entityEvents=id=>{
    const attrs=card.h?.states?.[id]?.attributes||{};
    if(!attrs.message||!attrs.start_time)return [];
    let start=String(attrs.start_time),end=String(attrs.end_time||"");
    if(attrs.all_day){
      start=start.slice(0,10);end=end?end.slice(0,10):start;
      if(end===start){
        const d=new Date(start+"T12:00:00");d.setDate(d.getDate()+1);
        end=[d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-");
      }
    }else{
      start=start.replace(" ","T");
      end=end.replace(" ","T");
    }
    return [{start,end,summary:String(attrs.message)}];
  };
  const parseCalendarResponse=(result,id)=>{
    // Native HA call_service returns {context,response:{entity:{events}}},
    // while REST and frontend HA versions can use different wrappers.
    const options=[
      result,result?.response,result?.service_response,
      result?.result,result?.result?.response,result?.result?.service_response,
      result?.data,result?.data?.response
    ];
    for(const value of options){
      if(Array.isArray(value))return value;
      if(Array.isArray(value?.events))return value.events;
      if(Array.isArray(value?.[id]?.events))return value[id].events;
      if(Array.isArray(value?.response?.[id]?.events))return value.response[id].events;
    }
    return null;
  };
  const mergeEvents=(a,b)=>{
    const found=new Set(),merged=[];
    for(const event of [...a,...b]){
      if(!event?.start||!event?.end)continue;
      const sig=[event.start,event.end,event.summary||event.title].join("|");
      if(found.has(sig))continue;
      found.add(sig);merged.push(event);
    }
    return merged;
  };
  const load=async(force=false)=>{
    if(!opened||disposed||ongoing)return;
    const id=calendarId(),now=Date.now();
    if(!force&&id===requestedCalendar&&now-lastFetch<300000)return;
    requestedCalendar=id;lastFetch=now;
    events=id?entityEvents(id):[];draw();
    if(!id){setStatus(cfg.calendar?"Kalender-Entität nicht vorhanden":"Google Familienkalender noch nicht mit Home Assistant verbunden");return;}
    if(typeof card.h?.callWS!=="function"&&typeof card.h?.callApi!=="function"){
      setStatus(events.length?"Familie · aktueller Termin aus HA":"Home Assistant nicht verbunden");return;
    }
    ongoing=true;const ticket=++serial,conn=card.h.connection;
    setStatus("Familienkalender · Lade Termine …");
    try{
      const begin=localDay(),end=add(begin,28);
      let received=null,lastError=null;
      if(typeof card.h?.callWS==="function"){
        try{
          const result=await card.h.callWS({
            type:"call_service",domain:"calendar",service:"get_events",
            target:{entity_id:id},
            service_data:{start_date_time:begin.toISOString(),end_date_time:end.toISOString()},
            return_response:true
          });
          received=parseCalendarResponse(result,id);
        }catch(err){lastError=err;}
      }
      // HA also exposes a read-only calendar REST endpoint. This fallback
      // avoids depending on a particular WS call_service response envelope.
      if((received===null||received.length===0)&&typeof card.h?.callApi==="function"){
        try{
          const uri="calendars/"+encodeURIComponent(id)+"?start="+
            encodeURIComponent(begin.toISOString())+"&end="+encodeURIComponent(end.toISOString());
          const result=await card.h.callApi("GET",uri);
          const other=parseCalendarResponse(result,id);
          if(other!==null)received=other;
        }catch(err){lastError=err;}
      }
      if(disposed||ticket!==serial||conn!==card.h?.connection)return;
      events=mergeEvents(received||[],entityEvents(id));
      const label=card.h?.states?.[id]?.attributes?.friendly_name||"Familienkalender";
      setStatus(label+" · "+events.length+" "+(events.length===1?"Termin":"Termine")+
        (received===null&&events.length?" · HA-Status":""));
      draw();
      if(lastError)console.debug("TAFA Übersicht: Kalenderabruf-Fallback",String(lastError?.message||lastError));
    }catch(err){
      if(disposed||ticket!==serial)return;
      events=mergeEvents(events,entityEvents(id));
      setStatus(events.length?"Familie · aktueller Termin aus HA":"Kalenderdaten derzeit nicht lesbar");
      draw();
      console.debug("TAFA Übersicht: Kalenderabruf",String(err?.message||err));
    }finally{if(ticket===serial)ongoing=false;}
  };

  const conditions={
    sunny:["☀️","Sonnig"],cloudy:["☁️","Bewölkt"],partlycloudy:["⛅","Wolkig"],
    rainy:["🌧️","Regen"],pouring:["🌧️","Regen"],snowy:["🌨️","Schnee"],
    snowy_rainy:["🌨️","Schneeregen"],fog:["🌫️","Nebel"],windy:["🌬️","Windig"],
    lightning:["⛈️","Gewitter"],lightning_rainy:["⛈️","Gewitter"],
    clear_night:["🌙","Klar"]
  };
  const numeric=e=>e&&Number.isFinite(Number(e.state))?Number(e.state):null;
  const validPower=e=>numeric(e)!==null&&["W","kW"].includes(String(e?.attributes?.unit_of_measurement||""))&&
    (e.attributes?.device_class==="power"||e.attributes?.state_class==="measurement");
  const findPower=(states,preferred,pattern)=>{
    for(const id of preferred)if(validPower(states[id]))return states[id];
    const key=Object.keys(states).find(id=>id.startsWith("sensor.")&&
      pattern.test(id+" "+String(states[id]?.attributes?.friendly_name||""))&&validPower(states[id]));
    return key?states[key]:null;
  };
  const fmtPower=e=>{
    const n=numeric(e),unit=String(e?.attributes?.unit_of_measurement||"");
    if(n===null||!["W","kW"].includes(unit))return "—";
    const w=unit==="kW"?n*1000:n;
    return Math.abs(w)>=1000?(w/1000).toLocaleString("de-DE",{maximumFractionDigits:2})+" kW":
      w.toLocaleString("de-DE",{maximumFractionDigits:0})+" W";
  };
  const weather=()=>{
    if(disposed||!opened)return;
    const h=card.h?.states||{};
    const weatherId=h["weather.home"]?"weather.home":
      Object.keys(h).find(id=>id.startsWith("weather.")&&!["unknown","unavailable"].includes(h[id]?.state));
    const wx=h[weatherId]||{};
    const cond=conditions[wx.state]||["🌤️","Wetter"];
    q("[data-today-icon]").textContent=cond[0];
    q("[data-today-desc]").textContent=cond[1];
    q("[data-today-label]").textContent=new Date().toLocaleDateString("de-DE",{weekday:"short",day:"numeric",month:"numeric"}).toUpperCase();
    const temp=Number(wx?.attributes?.temperature);
    const hasTemp=Number.isFinite(temp);
    q("[data-today-temp]").textContent=hasTemp?temp.toLocaleString("de-DE",{maximumFractionDigits:0})+"°":"—";
    const solar=findPower(h,[],/(?:solar|photovoltaik|pv|wechselrichter).*(?:power|leistung|output)/i);
    const grid=findPower(h,[],/(?:netz|grid|tibber.*pulse).*(?:power|leistung)/i);
    const price=h[Object.keys(h).find(id=>/strompreis|electricity_price|current_price/i.test(id)&&
      numeric(h[id])!==null&&/ct\/kWh|€\/kWh/.test(String(h[id].attributes?.unit_of_measurement||"")))];
    const p=numeric(price),priceUnit=String(price?.attributes?.unit_of_measurement||"");
    const values={
      solar:fmtPower(solar),grid:fmtPower(grid),
      outside:hasTemp?temp.toLocaleString("de-DE",{maximumFractionDigits:1})+" °C":"—",
      price:p===null?"—":(priceUnit==="€/kWh"?p*100:p).toLocaleString("de-DE",{maximumFractionDigits:2})+" ct/kWh"
    };
    for(const [name,value] of Object.entries(values)){
      const node=q('[data-oe="'+name+'"]');if(node&&node.textContent!==value)node.textContent=value;
    }
    for(let i=1;i<=5;i++){
      const date=new Date();date.setDate(date.getDate()+i);
      const item=q('[data-forecast-day="'+i+'"]');if(!item)continue;
      item.querySelector("small").textContent=["SO","MO","DI","MI","DO","FR","SA"][date.getDay()];
      const f=forecastData.find(x=>{
        const t=new Date(x.datetime||x.date||"");
        return Number.isFinite(t.getTime())&&t.getFullYear()===date.getFullYear()&&
          t.getMonth()===date.getMonth()&&t.getDate()===date.getDate();
      });
      item.querySelector(".hz-overview-forecast-icon").textContent=f?(conditions[f.condition]||["🌤️"])[0]:"·";
      const hi=Number(f?.temperature),lo=Number(f?.templow);
      item.querySelector(".hz-overview-forecast-temps").textContent=f&&Number.isFinite(hi)?
        hi.toLocaleString("de-DE",{maximumFractionDigits:0})+"°"+
        (Number.isFinite(lo)?" / "+lo.toLocaleString("de-DE",{maximumFractionDigits:0})+"°":""):"—";
    }
  };
  const refreshForecast=async(force=false)=>{
    if(disposed||!opened||forecastPending||!card.h?.callWS)return;
    if(!force&&Date.now()-forecastAt<900000)return;
    const states=card.h?.states||{};
    const id=states["weather.home"]?"weather.home":
      Object.keys(states).find(k=>k.startsWith("weather.")&&!["unknown","unavailable"].includes(states[k]?.state));
    if(!id)return;
    forecastAt=Date.now();forecastPending=true;
    const serialNumber=++forecastSerial,connection=card.h.connection;
    try{
      const result=await card.h.callWS({type:"call_service",domain:"weather",
        service:"get_forecasts",target:{entity_id:id},
        service_data:{type:"daily"},return_response:true});
      if(disposed||serialNumber!==forecastSerial||connection!==card.h.connection)return;
      for(const data of [result,result?.response,result?.service_response,result?.result,result?.result?.response]){
        const list=data?.[id]?.forecast||data?.forecast;
        if(Array.isArray(list)){forecastData=list;break;}
      }
      weather();
    }catch(err){console.debug("TAFA Ambient: Wettervorhersage",String(err?.message||err))}
    finally{if(serialNumber===forecastSerial)forecastPending=false;}
  };
  const playBeam=(reverse=false)=>{
    // Each view transition is a finite animation, never an always-on canvas.
    // Four separate comets depart actual positions on the sphere. As they
    // strike the panel, a temporary calendar grid lights up node-by-node.
    const reduced=typeof matchMedia==="function"&&matchMedia("(prefers-reduced-motion: reduce)").matches;
    if(reduced)return;
    const token=++beamToken;
    if(beamFrame!=null)cancelAnimationFrame(beamFrame);
    const hr=host.getBoundingClientRect(),sr=s.canvas?.getBoundingClientRect();
    const grid=q(".hz-overview-days");
    if(!sr||!grid||!hr.width||!hr.height)return;
    const tablet=host.dataset.tablet==="1";
    // Render the transient overlay at reduced resolution on Android.
    // The live sphere canvas is unchanged; only its *extra* FX layer
    // uses fewer pixels.
    const density=tablet?.75:Math.min(1.5,window.devicePixelRatio||1);
    particles.width=Math.round(hr.width*density);
    particles.height=Math.round(hr.height*density);
    const ctx=particles.getContext("2d",{alpha:true});
    if(!ctx)return;
    ctx.setTransform(density,0,0,density,0,0);
    // offsetLeft/Top are layout values: no transform-induced jump while
    // the panel is materializing from the bottom of the screen.
    const gx=panel.offsetLeft+grid.offsetLeft;
    const gy=panel.offsetTop+grid.offsetTop;
    const gw=grid.offsetWidth,gh=grid.offsetHeight;
    const origins=(tablet?
      [[.29,.65],[.75,.4],[.44,.77]]:
      [[.29,.65],[.75,.4],[.44,.77],[.6,.24]]
    ).map(([x,y])=>({x:sr.left+sr.width*x-hr.left,y:sr.top+sr.height*y-hr.top}));
    const targets=[
      {x:gx+4,y:gy+4},
      {x:gx+gw-4,y:gy+gh*.17},
      {x:gx+gw*.23,y:gy+gh-4},
      {x:gx+gw-4,y:gy+gh-4}
    ];
    const coords=origins.map((a,i)=>{
      const b=targets[i];
      const lift=(i%2===0?-1:1)*Math.max(24,Math.min(75,gw*.1));
      return {a,b,c:{x:(a.x+b.x)/2+lift,y:(a.y+b.y)/2-42},
        delay:130+i*95,duration:490+i*45};
    });
    const quad=(p,u)=>{
      const v=1-u;
      return {x:v*v*p.a.x+2*v*u*p.c.x+u*u*p.b.x,
        y:v*v*p.a.y+2*v*u*p.c.y+u*u*p.b.y};
    };
    const clamp=v=>Math.max(0,Math.min(1,v));
    const ease=v=>1-(1-v)*(1-v)*(1-v);
    const originalTotal=reverse?760:2070;
    const total=tablet?(reverse?510:1480):originalTotal;
    const started=performance.now();
    const interval=tablet?55:24;
    let previous=-1000;
    beam.setAttribute("viewBox","0 0 "+hr.width+" "+hr.height);
    const a=origins[2],b=targets[2];
    ray.setAttribute("d","M "+a.x+" "+a.y+" Q "+((a.x+b.x)/2-22)+" "+
      ((a.y+b.y)/2-55)+" "+b.x+" "+b.y);
    const length=ray.getTotalLength();
    beam.style.opacity="1";
    const loop=t=>{
      if(disposed||token!==beamToken||(!reverse&&!opened)||
        (reverse&&host.dataset.overview!=="closing"))return;
      const elapsed=t-started;
      if(elapsed-previous<interval&&elapsed<total){
        beamFrame=requestAnimationFrame(loop);return;
      }
      previous=elapsed;
      ctx.clearRect(0,0,hr.width,hr.height);
      const virtualTime=elapsed*originalTotal/total;
      const time=reverse?originalTotal-virtualTime:virtualTime;
      const finalFade=clamp((time-1190)/750);
      // A central trail accompanies the initial sphere pulse.
      const progress=ease(clamp((time-105)/680));
      const travel=length*progress;
      const p=ray.getPointAtLength(travel);
      ray.setAttribute("stroke-dasharray",Math.max(1,travel)+" "+(length+5));
      ray.style.opacity=String(Math.min(1,progress*4)*clamp((840-time)/240));
      spark.setAttribute("cx",String(p.x));spark.setAttribute("cy",String(p.y));
      spark.style.opacity=String(clamp(progress*7)*clamp((800-time)/230));
      // Thin calendar lattice: horizontal traces run left-to-right,
      // vertical traces follow, then each intersection sparkles.
      const latticeAlpha=1-finalFade;
      if(gw>0&&gh>0&&latticeAlpha>0){
        ctx.save();ctx.globalAlpha=latticeAlpha;
        ctx.lineWidth=.9;ctx.strokeStyle="rgba(106,226,246,.76)";
        ctx.shadowColor="#4ad9ff";ctx.shadowBlur=tablet?0:6;
        for(let row=0;row<=4;row++){
          const d=clamp((time-(530+row*83))/560);
          if(d<=0)continue;
          const y=gy+gh*row/4;
          ctx.beginPath();ctx.moveTo(gx,y);ctx.lineTo(gx+gw*ease(d),y);ctx.stroke();
        }
        for(let col=0;col<=7;col++){
          const d=clamp((time-(610+col*49))/515);
          if(d<=0)continue;
          const x=gx+gw*col/7;
          ctx.beginPath();ctx.moveTo(x,gy);ctx.lineTo(x,gy+gh*ease(d));ctx.stroke();
        }
        ctx.restore();
        // Nodes appear only after an animated ray reaches that crossing.
        for(let row=0;row<=4;row++)for(let col=0;col<=7;col++){
          const hit=695+row*93+col*53;
          const intensity=clamp((time-hit)/110)*clamp((hit+470-time)/420)*latticeAlpha;
          if(intensity<=0)continue;
          const x=gx+gw*col/7,y=gy+gh*row/4;
          ctx.save();ctx.globalAlpha=intensity;
          ctx.fillStyle="#d7ffff";ctx.shadowColor="#7dfaff";ctx.shadowBlur=tablet?0:12;
          ctx.beginPath();ctx.arc(x,y,1.4+intensity*1.4,0,Math.PI*2);ctx.fill();
          ctx.restore();
        }
      }
      // Shooting stars run FROM sphere nodes TO multiple grid targets,
      // each leaving a tapered luminous tail with a bright travelling head.
      for(const path of coords){
        const travel=clamp((time-path.delay)/path.duration);
        if(travel<=0||travel>=1)continue;
        const at=ease(travel),head=quad(path,at),tail=quad(path,Math.max(0,at-.23));
        const alpha=clamp(travel*12)*clamp((1-travel)*8);
        let stroke="rgba(120,245,250,"+(.75*alpha)+")";
        if(!tablet){
          const grad=ctx.createLinearGradient(tail.x,tail.y,head.x,head.y);
          grad.addColorStop(0,"rgba(36,215,239,0)");
          grad.addColorStop(.54,"rgba(80,236,250,"+(.25*alpha)+")");
          grad.addColorStop(1,"rgba(207,255,255,"+(.94*alpha)+")");
          stroke=grad;
        }
        ctx.save();ctx.lineWidth=1.5;ctx.strokeStyle=stroke;
        ctx.shadowColor="#6cf5ff";ctx.shadowBlur=tablet?0:9;
        ctx.beginPath();
        const segments=tablet?6:15;
        for(let k=0;k<=segments;k++){
          const u=Math.max(0,at-.23)+((at-Math.max(0,at-.23))*k/segments);
          const xy=quad(path,u);
          if(!k)ctx.moveTo(xy.x,xy.y);else ctx.lineTo(xy.x,xy.y);
        }
        ctx.stroke();ctx.fillStyle="#c9ffff";
        ctx.beginPath();ctx.arc(head.x,head.y,2.5,0,Math.PI*2);ctx.fill();
        ctx.restore();
      }
      if(elapsed<total)beamFrame=requestAnimationFrame(loop);
      else{beamFrame=null;beam.style.opacity="0";ctx.clearRect(0,0,hr.width,hr.height);}
    };
    beamFrame=requestAnimationFrame(loop);
  };
  const positionSphere=()=>{
    // Calculate a destination using *existing* layout rectangles before
    // changing to overview mode. The sphere stays in normal document flow;
    // only its compositor transform animates, so its live geometry never
    // jumps between relative and absolute positioning.
    const stage=host.querySelector(".hz-ambient-stage");
    const head=host.querySelector(".hz-ambient-head");
    if(!stage||!head||typeof stage.getBoundingClientRect!=="function")return;
    const sphere=stage.getBoundingClientRect();
    const header=head.getBoundingClientRect();
    const container=host.getBoundingClientRect();
    const panelTop=container.top+panel.offsetTop;
    if(!(sphere.width>0&&sphere.height>0&&panelTop>header.bottom))return;
    const available=Math.max(115,panelTop-header.bottom);
    // A Sphere silhouette has radius about 41% of the stage height.
    // Fit that silhouette above the weather panel, not the full canvas.
    // Keep it substantial: old min .33 made it tiny on 600px-wide PCs.
    const radiusAtOne=sphere.height*.41;
    const fit=(available-18)/Math.max(1,radiusAtOne*2);
    const scale=Math.max(.50,Math.min(.68,fit));
    const centerX=container.left+container.width/2;
    const radius=radiusAtOne*scale;
    // Bottom of the visible Sphere remains above the weather strip.
    const targetY=panelTop-14-radius;
    const centerY=Math.max(header.bottom+radius*.74,targetY);
    const dx=centerX-(sphere.left+sphere.width/2);
    const dy=centerY-(sphere.top+sphere.height/2);
    // Use per-display variables. The values are never stored globally.
    host.style.setProperty("--hz-sphere-dx",dx.toFixed(1)+"px");
    host.style.setProperty("--hz-sphere-dy",dy.toFixed(1)+"px");
    host.style.setProperty("--hz-sphere-scale",scale.toFixed(3));
  };
  const open=(reason="tap")=>{
    if(disposed||(reason==="sensor"&&s.profile&&(s.profile.enabled===false||s.profile.autoOpen===false)))return;
    lastTouch=Date.now();
    if(opened){
      if(reason==="sensor")openedBySensor=true;
      return;
    }
    openedBySensor=reason==="sensor";
    positionSphere();
    clearTimeout(collapseTimer);clearTimeout(revealTimer);
    beamToken++;if(beamFrame!=null)cancelAnimationFrame(beamFrame);
    panel.dataset.intro="1";
    opened=true;host.dataset.overview="open";panel.setAttribute("aria-hidden","false");
    host.dataset.overviewBuilding="1";
    // load() paints the entity-state calendar synchronously and skips
    // identical fetched results; no extra empty render on opening.
    weather();void load(true);void refreshForecast(true);
    requestAnimationFrame(()=>{if(opened&&!disposed)playBeam();});
    revealTimer=setTimeout(()=>{
      if(!disposed){
        panel.dataset.intro="0";
        host.dataset.overviewBuilding="0";
      }
    },2250);
  };
  const close=()=>{
    if(!opened)return;
    opened=false;openedBySensor=false;
    host.dataset.overviewBuilding="0";
    clearTimeout(revealTimer);clearTimeout(collapseTimer);
    beamToken++;if(beamFrame!=null)cancelAnimationFrame(beamFrame);
    beamFrame=null;beam.style.opacity="0";panel.dataset.intro="0";
    host.dataset.overview="closing";panel.setAttribute("aria-hidden","true");
    collapseTimer=setTimeout(()=>{
      if(!disposed&&!opened)host.dataset.overview="closed";
    },720);
    q(".hz-overview-config").hidden=true;serial++;ongoing=false;events=[];
  };
  const setForm=()=>{
    for(const field of ["calendar","presence","dismiss","idle"]){
      const control=q('[data-setting="'+field+'"]');
      if(control)control.value=String(cfg[field]??"");
    }
    const id=resolvePresenceId(card.h?.states||{});
    q("[data-presence-current]").textContent=cfg.presence?
      (id?"Manuell ausgewählt: "+id:"Eingetragener Sensor nicht gefunden: "+cfg.presence):
      (id?"Dieses Tablet: "+id:"Kein zugeordnetes Tablet gefunden – bitte Sensor manuell wählen");
    q(".hz-overview-config").hidden=false;
  };
  const onClick=event=>{
    if(disposed)return;
    const button=event.target.closest?.("[data-oa]");
    if(button&&panel.contains(button)){
      event.preventDefault();event.stopPropagation();lastTouch=Date.now();
      const act=button.dataset.oa;
      if(act==="close")close();
      if(act==="config")setForm();
      if(act==="cancel")q(".hz-overview-config").hidden=true;
      if(["prev","today","next"].includes(act)){
        monthOffset=act==="today"?0:monthOffset+(act==="prev"?-1:1);
        serial++;ongoing=false;events=[];lastFetch=0;draw();void load(true);
      }
      if(act==="save"){
        const cal=q('[data-setting="calendar"]').value.trim(),
          presence=q('[data-setting="presence"]').value.trim(),
          dismiss=q('[data-setting="dismiss"]').value,
          idle=Number(q('[data-setting="idle"]').value);
        if(cal&&!/^calendar\.[a-z0-9_]+$/.test(cal))return;
        if(presence&&!/^binary_sensor\.[a-z0-9_]+$/.test(presence))return;
        if(!["sensor","time","either"].includes(dismiss))return;
        if(!Number.isFinite(idle)||idle<0)return;
        cfg={calendar:cal,presence,dismiss,idle};
        if(s.profile&&s.deviceId&&card.h?.callWS){
          const profile={...s.profile,...cfg};
          void card.h.callWS({type:"tablet_assist_for_alexa/ambient_profiles",action:"save",
            device_id:s.deviceId,revision:s.profileRevision||0,profile}).then(result=>{
              if(disposed)return;s.profile=result.profile;s.profileRevision=result.revision;
              setStatus("Geräteprofil gespeichert");
            }).catch(error=>{
              if(disposed)return;cfg={...cfg,...s.profile};
              setStatus("Speichern fehlgeschlagen: "+String(error.message||error));
            });
        }else{try{localStorage.setItem(STORE,JSON.stringify(cfg));}catch{}}
        serial++;ongoing=false;requestedCalendar="";lastFetch=0;
        wasPresent=false;boundPresenceId="";q(".hz-overview-config").hidden=true;void load(true);
      }
      return;
    }
    if(panel.contains(event.target)){
      lastTouch=Date.now();
      event.stopPropagation();
      return;
    }
    if(event.target.closest?.(".hz-ambient-info,.hz-ambient-exit"))return;
    if(!opened&&!s.suppressClick){
      open("tap");
      event.stopPropagation();
    }
  };
  host.addEventListener("click",onClick);
  const onPresence=event=>{
    const id=card._tafaLocalVoice?.deviceId||
      card._tafaLocalVoice?.wake_device_id||card._tafaLocalVoice?.device_id;
    if(!id||event?.detail?.device_id!==id)return;
    if(event.detail.active===true)open("sensor");
    else if(event.detail.active===false&&openedBySensor&&cfg.dismiss!=="time")close();
  };
  window.addEventListener("tafa:ambient-presence",onPresence);
  s.overview={
    open,close,
    applyProfile(profile){
      if(disposed||!profile)return;
      const changed=cfg.calendar!==profile.calendar;
      cfg={...cfg,calendar:profile.calendar||"",presence:profile.presence||"",
        dismiss:profile.dismiss||"sensor",
        idle:Number.isFinite(Number(profile.idle))?Number(profile.idle):55,
        enabled:profile.enabled!==false,autoOpen:profile.autoOpen!==false};
      if(profile.enabled===false){close();return;}
      wasPresent=false;boundPresenceId="";
      if(changed){serial++;ongoing=false;requestedCalendar="";lastFetch=0;void load(true);}
    },
    update(){
      if(disposed)return;
      const states=card.h?.states||{};
      const presenceId=resolvePresenceId(states);
      if(presenceId!==boundPresenceId){
        boundPresenceId=presenceId;
        wasPresent=false;
      }
      const state=presenceId?String(states[presenceId]?.state||"").toLowerCase():"";
      const present=["on","present","detected","home"].includes(state);
      const free=["off","free","clear","frei","not_home"].includes(state);
      if(present&&!wasPresent&&cfg.enabled!==false&&cfg.autoOpen!==false)open("sensor");
      else if(free&&wasPresent&&opened&&cfg.dismiss!=="time")close();
      wasPresent=present;
      if(!opened)return;
      const now=Date.now();
      if(s.phase!=="idle"||host.dataset.ambientInfoState==="open")lastTouch=now;
      // In sensor mode the sensor owns an automatically opened view.
      // A manual tap while the sensor is still "Frei" uses the optional
      // timer as a fallback. In time/either mode the timer always applies.
      const useTimer=cfg.dismiss==="time"||cfg.dismiss==="either"||
        (cfg.dismiss==="sensor"&&!openedBySensor);
      if(useTimer&&cfg.idle>0&&now-lastTouch>=cfg.idle*1000)close();
      if(now-lastWeather>10000){lastWeather=now;weather();}
      if(now-forecastAt>900000&&!forecastPending)void refreshForecast();
      if(now-lastFetch>60000&&!ongoing)void load();
    },
    dispose(){
      disposed=true;serial++;beamToken++;forecastSerial++;
      host.dataset.overviewBuilding="0";
      clearTimeout(revealTimer);clearTimeout(collapseTimer);
      if(beamFrame!=null)cancelAnimationFrame(beamFrame);
      host.removeEventListener("click",onClick);
      window.removeEventListener("tafa:ambient-presence",onPresence);
      particles.remove();panel.remove();beam.remove();bloom.remove();style.remove();
    }
  };
  // The device profile may arrive before the optional overview module loads.
  if(s.profile)s.overview.applyProfile(s.profile);
  host.dataset.overview="closed";
}
