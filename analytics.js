/* GA4: opt-in only; no form values, names, emails or query strings. */
(() => {
  'use strict';
  const tag = document.currentScript;
  const id = tag.dataset.measurementId;
  const site = tag.dataset.site;
  const key = 'portfolio_analytics_consent_v1_' + site;
  const production = location.hostname === tag.dataset.host;
  const preview = new URLSearchParams(location.search).get('analytics_preview') === '1';
  if (!production && !preview) return;
  let allowed = false, started = false, viewed = '';
  const read = () => { try { return localStorage.getItem(key); } catch (_) { return null; } };
  const write = v => { try { localStorage.setItem(key, v); } catch (_) {} };
  const cleanUrl = () => location.origin + location.pathname;
  const event = (name, params = {}) => {
    if (allowed && production && window.gtag) window.gtag('event', name, {send_to:id, portfolio_site:site, ...params});
  };
  function start() {
    allowed = true;
    window['ga-disable-' + id] = false;
    if (started || !production) return;
    started = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', id, {
      send_page_view:false, allow_google_signals:false,
      allow_ad_personalization_signals:false, page_location:cleanUrl(),
      page_referrer:document.referrer ? new URL(document.referrer).origin : '',
      cookie_flags:'SameSite=Lax;Secure', cookie_expires:60*60*24*90
    });
    const script = document.createElement('script'); script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
    document.head.append(script);
    pageView();
  }
  function pageView() {
    const active = document.querySelector('#menu button.active');
    const section = active ? active.textContent.trim() : document.title;
    if (section === viewed) return;
    viewed = section;
    event('page_view', {page_title:section, page_location:cleanUrl(), content_group:site});
    if (active) event('dashboard_section_view', {section_name:section});
  }
  const style = document.createElement('style');
  style.textContent = '#pa-notice{position:fixed;bottom:16px;left:16px;right:16px;max-width:650px;margin:auto;padding:18px;background:#24211c;color:#f8efd9;border:1px solid #c7a569;box-shadow:0 4px 24px #0005;z-index:100000;font:14px/1.6 system-ui,sans-serif;text-align:left}#pa-notice p{margin:6px 0 12px;color:inherit;font:inherit}#pa-notice button,#pa-settings{font:inherit;cursor:pointer}#pa-notice button{padding:8px 14px;margin:4px 6px 0 0;border:1px solid #c7a569;background:#f6edd9;color:#24211c}#pa-notice a{color:#e7c88a}#pa-notice details{margin:8px 0}#pa-settings{display:block;margin:12px auto;padding:6px 12px;background:transparent;color:inherit;border:1px solid currentColor;font-size:12px}';
  document.head.append(style);
  function notice() {
    if (document.getElementById('pa-notice')) return;
    const box = document.createElement('section'); box.id='pa-notice';
    box.setAttribute('aria-label','방문 분석 설정');
    box.innerHTML='<strong>포트폴리오 방문 분석</strong><p>동의하시면 Google Analytics로 방문·페이지 열람·주요 클릭을 측정합니다. 거절해도 모든 기능을 이용할 수 있습니다.</p><details><summary>수집 내용과 설정 안내</summary><p>쿠키 기반 식별자, 접속 환경, 열람 페이지와 주요 클릭을 Google이 처리합니다. 이름·이메일·입력값은 이벤트에 넣지 않습니다. 광고 개인화는 사용하지 않습니다. 이 브라우저의 선택은 저장되며 아래 방문 분석 설정에서 변경할 수 있습니다. 철회 후 신규 수집을 중단하고 이 사이트의 분석 쿠키를 삭제합니다. 기존 수집 자료가 즉시 삭제되는 것은 아닙니다.</p><a href="https://policies.google.com/technologies/partner-sites?hl=ko" target="_blank" rel="noopener">Google의 데이터 처리 안내</a></details><button type="button" data-choice="yes">분석 동의</button><button type="button" data-choice="no">거절 / 철회</button>';
    box.addEventListener('click', e => {
      const choice = e.target.closest('[data-choice]'); if (!choice) return;
      const yes = choice.dataset.choice === 'yes'; write(yes?'yes':'no');
      if (yes) start();
      else {
        allowed=false; window['ga-disable-'+id]=true;
        const domains=[location.hostname,'.'+location.hostname];
        const parts=location.hostname.split('.'); if(parts.length>2) domains.push('.'+parts.slice(-2).join('.'));
        document.cookie.split(';').forEach(c=>{const n=c.split('=')[0].trim(); if(!/^_ga(?:_|$)|^_gid$/.test(n))return;
          for(const domain of domains) document.cookie=n+'=; Max-Age=0; path=/; domain='+domain;
          document.cookie=n+'=; Max-Age=0; path=/';
        });
      }
      box.remove();
    });
    document.body.append(box);
  }
  const settings=document.createElement('button');settings.id='pa-settings';settings.type='button';settings.textContent='방문 분석 설정';settings.addEventListener('click',notice);
  (document.querySelector('footer')||document.body).append(settings);
  document.addEventListener('click', e=>{
    const target=e.target.closest('a,button'); if(!target || target.closest('#pa-notice') || target.id==='pa-settings') return;
    if (target.closest('#menu')) { setTimeout(pageView,0); return; }
    const href=target.getAttribute('href');
    if(href) {
      let url;try{url=new URL(href,location.href);}catch(_){return;}
      if(!/^https?:$/.test(url.protocol)) return;
      if(/\.pdf$/i.test(url.pathname)) event('portfolio_document_click',{document_name:url.pathname.split('/').pop(),action:target.hasAttribute('download')?'download':'open'});
      else if(site==='parry_hero' && url.origin===location.origin && url.pathname==='/') event('game_link_click');
      else if(url.origin!==location.origin) event('outbound_link_click',{link_domain:url.hostname});
    }
    if(target.hasAttribute('data-download')) event('dashboard_export_click',{export_index:target.getAttribute('data-download')});
    const mode={startBtn:'normal',endlessStart:'endless',again:'retry'}[target.id];
    if(mode) event('game_start_click',{game_mode:mode});
  });
  document.addEventListener('change',e=>{if(site==='business_bi' && ['project','period','unit'].includes(e.target.id)) event('dashboard_filter_change',{filter_name:e.target.id});});
  document.addEventListener('scroll',()=>{if(allowed && !document.body.dataset.paScrolled && window.scrollY+innerHeight>=document.documentElement.scrollHeight*.9){document.body.dataset.paScrolled='1';event('scroll',{percent_scrolled:90});}},{passive:true});
  if(read()==='yes') start(); else if(read()!=='no') notice();
})();

