import React from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import {LiquidGlassRenderer} from '../upstream/D1/src/renderer';
import {preset} from '../upstream/D1/src/params';
import {GlassRenderer} from '../upstream/D2/src/GlassRenderer';
import {DEFAULTS, SHADOW_PAD} from '../upstream/D2/src/defaults';
import LiquidGlass from '../upstream/D3/src/index';

const W=1920, H=1080;
const canvas=(w=W,h=H)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
const nextFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
const loadImage=async(src:string)=>{const im=new Image();im.src=src;await im.decode();return im;};

export async function setup(spec:any) {
  const bg=await loadImage(spec.backdropData);
  const [x,y,w,h]=spec.rectangle;
  const px=x-32,py=y-32,pw=w+64,ph=h+64;
  document.body.innerHTML='';
  document.body.style.cssText='margin:0;overflow:hidden;width:1920px;height:1080px';
  const style=document.createElement('style');
  style.textContent=`*{animation:none!important;transition:none!important} .relative{position:relative}.opacity-0{opacity:0}.opacity-20{opacity:.2}.opacity-100{opacity:1}.pointer-events-none{pointer-events:none}.bg-black{background:black}.mix-blend-overlay{mix-blend-mode:overlay}.glass{width:100%;height:100%;box-sizing:border-box}`;
  document.head.appendChild(style);
  const bgEl=document.createElement('img'); bgEl.src=spec.backdropData;
  bgEl.style.cssText='position:absolute;left:0;top:0;width:1920px;height:1080px';document.body.appendChild(bgEl);
  await bgEl.decode();
  const probe=canvas(); const gl=probe.getContext('webgl2');
  if(!gl)throw Error('WebGL2 is unavailable');
  const ext=gl.getExtension('WEBGL_debug_renderer_info');
  const backend=ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
  gl.getExtension('WEBGL_lose_context')?.loseContext();
  let settings:any; let draw:any;
  if(spec.tool==='D1') {
    // Odd photo widths have center x=959.5. Match this with a 1919-pixel native canvas.
    const nativeWidth=2*x+w;
    const layer=canvas(nativeWidth,H), renderer=new LiquidGlassRenderer(layer,{pixelRatio:1,strict:true});
    renderer.resize(nativeWidth,H);
    const upload=canvas(nativeWidth,H); const uc=upload.getContext('2d')!;
    // Upstream uploads with UNPACK_FLIP_Y_WEBGL=false; invert the upload rows explicitly.
    uc.translate(0,H);uc.scale(1,-1);uc.drawImage(bg,0,0);
    renderer.setBackdrop({kind:'canvas',canvas:upload});
    const p=preset(spec.preset==='frosted'?'regular':'clear');p.halfSize=[pw/2,ph/2];
    if(spec.preset==='strong-edge'){p.innerRefractAmount*=2;p.outerRefractAmount*=2;}
    renderer.render(p);
    const rg=layer.getContext('webgl2')!;const program=rg.getParameter(rg.CURRENT_PROGRAM);
    const area=rg.getUniformLocation(program,'uElementHalfSizePx');
    if(area===null)throw Error('Missing native drawing-area uniform');
    rg.uniform2f(area,nativeWidth/2,H/2);
    settings={...p,adapter:{drawingAreaUniform:[nativeWidth/2,H/2],uploadRowsFlipped:true,nativeCanvas:[nativeWidth,H]},cornerShape:'native superellipse, exponent 6.5'};
    draw=(kind:string)=>{
      const full=canvas(),ctx=full.getContext('2d')!;ctx.drawImage(bg,0,0);
      if(kind!=='off'){
        renderer.render(kind==='refraction-off'?{...p,innerRefractAmount:0,outerRefractAmount:0}:p);
        ctx.drawImage(layer,0,0); // copy synchronously before yielding to the browser
        if(rg.getError()!==rg.NO_ERROR)throw Error('D1 WebGL error');
      }
      return full.toDataURL('image/png');
    };
  } else if(spec.tool==='D2') {
    const renderer=new GlassRenderer(), source=canvas(); source.getContext('2d')!.drawImage(bg,0,0);
    const p={...DEFAULTS,blurAmount:spec.preset==='frosted'?.5:.1,refraction:spec.preset==='strong-edge'?.69:.35};
    settings={...p,shadowPadding:SHADOW_PAD,blurPasses:6,cornerShape:'native rounded rectangle'};
    draw=(kind:string)=>{
      const full=canvas(),ctx=full.getContext('2d')!;ctx.drawImage(bg,0,0);
      if(kind!=='off'){
        renderer.uploadAndBlur(source,px-SHADOW_PAD,py-SHADOW_PAD,pw+SHADOW_PAD*2,ph+SHADOW_PAD*2,p.blurAmount);
        renderer.clear();renderer.renderGlassPanel(kind==='refraction-off'?{...p,refraction:0}:p,pw,ph,1);
        if(renderer.contextLost||renderer.gl.getError()!==renderer.gl.NO_ERROR)throw Error('D2 WebGL error or lost context');
        ctx.drawImage(renderer.canvas,px-SHADOW_PAD,py-SHADOW_PAD);
      }
      return full.toDataURL('image/png');
    };
  } else {
    const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
    const p={blurAmount:spec.preset==='frosted'?.375:.0625,displacementScale:spec.preset==='strong-edge'?70:35,
      elasticity:0,saturation:140,aberrationIntensity:2,cornerRadius:32,padding:'0px',mode:'standard' as const,
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
  }
  (window as any).renderCase=draw;
  return {settings,backend,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,zoom:visualViewport!.scale},pane:[px,py,pw,ph]};
}
