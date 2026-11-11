import React from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import LiquidGlass from '../upstream/D3/src/index';
const nextFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
const loadImage=async(src:string)=>{const im=new Image();im.src=src;await im.decode();return im;};
export async function setup(spec:any) {
  const [W,H]=spec.canvas, scale=Math.min(W,H)/1080;
  const [x,y,w,h]=spec.rectangle;
  const px=x-32*scale, py=y-32*scale, pw=w+64*scale, ph=h+64*scale;
  document.body.innerHTML='';
  document.body.style.cssText=`margin:0;overflow:hidden;width:${W}px;height:${H}px`;
  const style=document.createElement('style');
  style.textContent=`*{animation:none!important;transition:none!important} .relative{position:relative}.opacity-0{opacity:0}.opacity-20{opacity:.2}.opacity-100{opacity:1}.pointer-events-none{pointer-events:none}.bg-black{background:black}.mix-blend-overlay{mix-blend-mode:overlay}.glass{width:100%;height:100%;box-sizing:border-box}`;
  document.head.appendChild(style);
  const bgEl=document.createElement('img'); bgEl.src=spec.backdropData;
  bgEl.style.cssText=`position:absolute;left:0;top:0;width:${W}px;height:${H}px`;document.body.appendChild(bgEl);
  await bgEl.decode();
  const gl=document.createElement('canvas').getContext('webgl2');
  if(!gl)throw Error('WebGL2 unavailable');
  const ext=gl.getExtension('WEBGL_debug_renderer_info');
  const backend=ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
  gl.getExtension('WEBGL_lose_context')?.loseContext();
  let settings:any; let draw:any;
    const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
    const p={blurAmount:(16*scale-4)/32,displacementScale:35*scale,
      elasticity:0,saturation:140,aberrationIntensity:2,cornerRadius:32*scale,padding:'0px',mode:'standard' as const,
      globalMousePos:{x:0,y:0},mouseOffset:{x:0,y:0},overLight:false};
    settings={...p,cssBlurPx:4+p.blurAmount*32,cornerShape:'CSS rounded rectangle',utilityCSS:'local position/opacity/blend rules',pointer:'fixed outside pane'};
    draw=async(kind:string)=>{
      flushSync(()=>root.render(kind==='off'?null:<LiquidGlass {...p} displacementScale={kind==='refraction-off'?0:p.displacementScale}
        style={{position:'absolute',left:x+w/2,top:y+h/2,width:pw,height:ph}}>
        <div style={{width:pw,height:ph}} />
      </LiquidGlass>));
      await nextFrame();await nextFrame();
      const refs=[...document.querySelectorAll('feImage')].map(e=>e.getAttribute('href')||e.getAttribute('xlink:href')).filter(Boolean);
      await Promise.all([...new Set(refs)].map(src=>loadImage(src!)));
      await document.fonts.ready;await nextFrame();
      if(kind!=='off'){
        const box=document.querySelector('.glass')!.getBoundingClientRect();
        if(Math.abs(box.x-px)>.1||Math.abs(box.y-py)>.1||Math.abs(box.width-pw)>.1||Math.abs(box.height-ph)>.1)
          throw Error('D3 pane layout differs from requested geometry');
      }
      return null; // Python captures the complete browser scene.
    };
  (window as any).renderCase=draw;
  return {settings,backend,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,zoom:visualViewport!.scale},pane:[px,py,pw,ph]};
}
