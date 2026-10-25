// Poses d'exercice du mannequin Quaternius (squelette « DEF-… »), calculées par cinématique inverse à deux os.
// poser(nom, u, t) : nom = exercice (pompes | gainage | squat | suspension) ou nom d'un clip ; u = 0 → 1 (position haute → basse).
function creerPoses(THREE, corps, m, clips, scene, mat){
  const os={};m.traverse(o=>{if(o.isBone)os[o.name]=o;});
  const B=n=>os['DEF-'+n.replace('.','')];
  const mix=new THREE.AnimationMixer(m);
  const V=(x,y,z)=>new THREE.Vector3(x,y,z);
  const wp=o=>{o.updateWorldMatrix(true,false);return new THREE.Vector3().setFromMatrixPosition(o.matrixWorld);};
  const wq=o=>{o.updateWorldMatrix(true,false);return o.getWorldQuaternion(new THREE.Quaternion());};
  // oriente l'os pour que son axe +Y (vers l'enfant) pointe dans la direction monde « dir »
  function aim(b,dir){const q=wq(b);const y=V(0,1,0).applyQuaternion(q);const d=new THREE.Quaternion().setFromUnitVectors(y,dir.clone().normalize());
    const pq=wq(b.parent).invert();b.quaternion.copy(pq.multiply(d.multiply(q)));b.updateWorldMatrix(false,true);}
  // deux os : l'extrémité « end » va en T, le coude / genou part du côté de « pole »
  function ik(up,lo,end,T,pole){const S=wp(up),E0=wp(lo),H0=wp(end);const a=S.distanceTo(E0),b=E0.distanceTo(H0);
    const D=T.clone().sub(S);const d=Math.min(D.length(),(a+b)*.999);const n=D.normalize();
    const ca=(a*a+d*d-b*b)/(2*a*d),sa=Math.sqrt(Math.max(0,1-ca*ca));
    const pm=pole.clone().sub(n.clone().multiplyScalar(pole.dot(n))).normalize();
    const E=S.clone().add(n.clone().multiplyScalar(a*ca)).add(pm.multiplyScalar(a*sa));
    aim(up,E.clone().sub(S));aim(lo,T.clone().sub(wp(lo)));}
  const cote=['L','R'],sg={L:1,R:-1};
  const bras=s=>[B('upper_arm.'+s),B('forearm.'+s),B('hand.'+s)];
  const jambe=s=>[B('thigh.'+s),B('shin.'+s),B('foot.'+s)];
  function base(nom,t){mix.stopAllAction();const c=THREE.AnimationClip.findByName(clips,nom);if(!c)return false;mix.clipAction(c).play();mix.setTime(t||0);m.updateMatrixWorld(true);return true;}
  // barre de traction (suspension)
  const BARRE=2.32,barre=new THREE.Group();const metal=new THREE.MeshStandardMaterial({color:0x1b1715,roughness:.35,metalness:.8});
  const cyl=(r,h)=>new THREE.CylinderGeometry(r,r,h,24);
  [-.78,.78].forEach(x=>{const p=new THREE.Mesh(cyl(.035,BARRE+.05),metal);p.position.set(x,(BARRE+.05)/2,0);p.castShadow=true;barre.add(p);});
  const tb=new THREE.Mesh(cyl(.022,1.62),metal);tb.rotation.z=Math.PI/2;tb.position.y=BARRE;tb.castShadow=true;barre.add(tb);barre.visible=false;scene.add(barre);
  function poser(nom,u,t){
    corps.position.set(0,0,0);corps.rotation.set(0,0,0);corps.updateMatrixWorld(true);barre.visible=false;
    if(!['pompes','gainage','squat','suspension'].includes(nom)){base(nom,t);return;}
    base('Idle_Loop',0);
    if(nom=='pompes'||nom=='gainage'){
      // hauteur d'épaule voulue (bras tendus → bras pliés) ; on cherche l'inclinaison du corps qui la donne, pivot sur la pointe des pieds
      // jambes tendues, pieds à plat vers l'avant : une fois le corps basculé, les orteils se retrouvent plantés au sol
      cote.forEach(s=>{const [a,b,h]=jambe(s);aim(a,V(sg[s]*.04,-1,0));aim(b,V(sg[s]*.02,-1,0));aim(h,V(0,-.35,.94));});
      const hv=nom=='pompes'?THREE.MathUtils.lerp(.5,.24,u):.27;let rx=Math.PI/2-.3;
      const place=()=>{corps.position.set(0,0,0);corps.rotation.x=rx;corps.updateMatrixWorld(true);const toe=wp(B('toe.L'));
        corps.position.y=.025-toe.y;corps.position.z=-toe.z;corps.updateMatrixWorld(true);};
      for(let i=0;i<6;i++){place();const S=wp(B('upper_arm.L')),L=Math.hypot(S.y,S.z);rx-=Math.asin(Math.max(-1,Math.min(1,(hv-S.y)/L)));}
      place();
      cote.forEach(s=>{const [a,b,h]=bras(s);const S=wp(a);
        const T=nom=='pompes'?V(S.x*1.35,.04,S.z+.04):V(S.x*.9,.035,S.z+.3);
        const pole=nom=='pompes'?V(sg[s]*1,.2,-.7):V(sg[s]*.2,-1,-.4);ik(a,b,h,T,pole);});
    }else if(nom=='squat'){
      // mélange « debout » → « assis » (vrai clip), puis on retire la chaise : pieds recalés au sol, buste penché, bras devant
      mix.stopAllAction();const ai=mix.clipAction(THREE.AnimationClip.findByName(clips,'Idle_Loop')),as=mix.clipAction(THREE.AnimationClip.findByName(clips,'Sitting_Idle_Loop'));
      ai.reset().play();as.reset().play();ai.setEffectiveWeight(1-u);as.setEffectiveWeight(u);mix.setTime(0);m.updateMatrixWorld(true);
      const F={};cote.forEach(s=>{F[s]=wp(B('foot.'+s));});const fy={};cote.forEach(s=>{fy[s]=V(0,1,0).applyQuaternion(wq(B('foot.'+s)));});
      corps.position.set(0,-.06*u,-.12*u);corps.rotation.x=.38*u;corps.updateMatrixWorld(true);
      cote.forEach(s=>{const [a,b,h]=jambe(s);ik(a,b,h,V(F[s].x,F[s].y,F[s].z+.05*u),V(sg[s]*.35,0,1));aim(h,fy[s]);});
      cote.forEach(s=>{const [a,b]=bras(s);const f=V(sg[s]*.1,-.25+.25*u,1);aim(a,f);aim(b,f);});
    }else if(nom=='suspension'){
      barre.visible=true;const S0=wp(B('upper_arm.L')).y;
      corps.position.y=BARRE-THREE.MathUtils.lerp(.5,.16,u)-S0;corps.updateMatrixWorld(true);
      cote.forEach(s=>{const [a,b,h]=bras(s);ik(a,b,h,V(sg[s]*.3,BARRE-.02,0),V(sg[s]*1,0,-.35));});
      cote.forEach(s=>{const [a,b,h]=jambe(s);const H=wp(a);ik(a,b,h,V(H.x,H.y-.8,H.z+.12),V(0,0,1));});
    }
  }
  return {poser,barre,B,wp};
}
