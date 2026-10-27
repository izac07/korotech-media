// Poses du mannequin Mixamo « Y Bot » (squelette « mixamorig… ») : vraies animations de sport filmées en capture de mouvement.
// poser(nom, u, t) : nom = clé d'animation (pompes | pompes_diamant | gainage | squat | burpee | jumping_jacks | abdos | crunch_velo), t = temps dans la scène.
// Pompes diamant : animation « Push Up » + mains ramenées en losange sous la poitrine par cinématique inverse (Mixamo n'a pas de pompes diamant).
function creerPosesMixamo(THREE, corps, m, clips, scene, mat){
  // le Y Bot a deux maillages (surface + articulations) avec chacun son jeu d'os du même nom : on retouche le premier, puis on recopie
  const tous={};m.traverse(o=>{if(o.isBone){const k=o.name.replace(/^mixamorig\d*:?/,'');(tous[k]=tous[k]||[]).push(o);}});
  const B=(n,i)=>(tous[n]||[])[i||0];
  const jeux=Math.max(...Object.values(tous).map(l=>l.length));
  const mix=new THREE.AnimationMixer(m);
  const V=(x,y,z)=>new THREE.Vector3(x,y,z);
  const wp=o=>{o.updateWorldMatrix(true,false);return new THREE.Vector3().setFromMatrixPosition(o.matrixWorld);};
  const wq=o=>{o.updateWorldMatrix(true,false);return o.getWorldQuaternion(new THREE.Quaternion());};
  function aim(b,dir){const q=wq(b);const y=V(0,1,0).applyQuaternion(q);const d=new THREE.Quaternion().setFromUnitVectors(y,dir.clone().normalize());
    const pq=wq(b.parent).invert();b.quaternion.copy(pq.multiply(d.multiply(q)));b.updateWorldMatrix(false,true);}
  function ik(up,lo,end,T,pole){const S=wp(up),E0=wp(lo),H0=wp(end);const a=S.distanceTo(E0),b=E0.distanceTo(H0);
    const D=T.clone().sub(S);const d=Math.min(D.length(),(a+b)*.999);const n=D.normalize();
    const ca=(a*a+d*d-b*b)/(2*a*d),sa=Math.sqrt(Math.max(0,1-ca*ca));
    const pm=pole.clone().sub(n.clone().multiplyScalar(pole.dot(n))).normalize();
    const E=S.clone().add(n.clone().multiplyScalar(a*ca)).add(pm.multiplyScalar(a*sa));
    aim(up,E.clone().sub(S));aim(lo,T.clone().sub(wp(lo)));}
  const barre=new THREE.Group();barre.visible=false;
  const ALIAS={Idle_Loop:'idle',pompes_diamant:'pompes'};
  function poser(nom,u,t,tt){
    const cle=ALIAS[nom]||nom,c=clips[cle]||clips.idle;
    mix.stopAllAction();mix.clipAction(c).play();mix.setTime(Math.max(0,t||0)%c.duration);m.updateMatrixWorld(true);
    if(nom=='pompes_diamant'){
      // mains jointes sous le sternum, au sol ; le coude garde le plan de l'animation (il part vers l'arrière)
      // les cibles sont calculées sur le premier jeu d'os, puis chaque jeu (surface, articulations) est plié vers les mêmes cibles
      const sL=wp(B('LeftArm')),sR=wp(B('RightArm')),lat=sL.clone().sub(sR).normalize(),cib={};
      for(const s of ['Left','Right']){const S=wp(B(s+'Arm')),H=wp(B(s+'Hand')),E=wp(B(s+'ForeArm')),sg=s=='Left'?1:-1;
        // le losange se forme sous la poitrine : on garde la profondeur et la hauteur de la main d'origine
        const fw=H.clone().sub(S);fw.sub(lat.clone().multiplyScalar(fw.dot(lat)));
        cib[s]=[S.clone().sub(lat.clone().multiplyScalar(sg*(sL.distanceTo(sR)/2-.07))).add(fw),E.clone().sub(S).add(lat.clone().multiplyScalar(sg*.15))];}
      for(let i=0;i<jeux;i++)for(const s of ['Left','Right']){const up=B(s+'Arm',i),lo=B(s+'ForeArm',i),h=B(s+'Hand',i);if(up&&lo&&h)ik(up,lo,h,cib[s][0],cib[s][1]);}
      m.updateMatrixWorld(true);
    }
  }
  return {poser,barre,B,wp};
}
