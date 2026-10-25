import React from 'react';
import { roundedBox } from '../assets/geometry';
import { glassMaterial, paint, TRAIN_COLORS as C } from './materials';
import { Wheel } from './Wheel';
import { GAUGE_HALF, LOCO, RAIL_TOP } from './layout';

/**
 * Sarı-turuncu oyuncak lokomotif.
 * Yerel koordinatlar: +X ön, Y yukarı, origin ray ekseninde zemin hizası.
 * children → kabin içeriği (Pandi), lokomotifle birlikte hareket eder.
 */
export const Locomotive: React.FC<{
  wheelDistance: number;
  steeringTurn?: number;
  children?: React.ReactNode;
}> = ({ wheelDistance, steeringTurn = 0, children }) => {
  const yellow = paint(C.locoYellow);
  const orange = paint(C.locoOrange);
  const chassis = paint(C.chassis, { roughness: 0.6 });
  const cream = paint('#FFF1C9');
  const dark = paint('#1E1A1C', { roughness: 0.35 });
  const pink = paint('#FF9AAE', { roughness: 0.8 });
  const white = paint('#FFFFFF', { roughness: 0.3 });

  const boilerY = 2.07;
  const driveY = RAIL_TOP + LOCO.driveWheelR;
  const frontY = RAIL_TOP + LOCO.frontWheelR;
  const z = GAUGE_HALF;

  return (
    <group>
      {/* --- Şasi --- */}
      <mesh position={[-0.1, 0.95, 0]} geometry={roundedBox(6.4, 0.34, 2.2, 0.2, 0.06)} material={chassis} castShadow receiveShadow />
      {/* ön tampon kirişi ve tamponlar */}
      <mesh position={[3.0, 0.95, 0]} geometry={roundedBox(0.3, 0.42, 2.4, 0.1, 0.05)} material={paint(C.red)} castShadow />
      {[-0.75, 0.75].map((zz) => (
        <mesh key={zz} position={[3.2, 0.95, zz]} rotation={[0, 0, Math.PI / 2]} material={dark}>
          <cylinderGeometry args={[0.13, 0.13, 0.18, 20]} />
        </mesh>
      ))}

      {/* --- Tekerlekler --- */}
      {[1, -1].map((side) => (
        <group key={side}>
          <Wheel radius={LOCO.driveWheelR} angle={wheelDistance / LOCO.driveWheelR} position={[-2.0, driveY, side * z]} side={side as 1 | -1} />
          <Wheel radius={LOCO.driveWheelR} angle={wheelDistance / LOCO.driveWheelR} position={[-0.35, driveY, side * z]} side={side as 1 | -1} />
          <Wheel radius={LOCO.frontWheelR} angle={wheelDistance / LOCO.frontWheelR} position={[1.95, frontY, side * z]} side={side as 1 | -1} />
          {/* biyel kolu: iki büyük tekerleği bağlar, tekerlekle birlikte döner */}
          {(() => {
            const a = wheelDistance / LOCO.driveWheelR;
            const r = LOCO.driveWheelR * 0.55;
            const dx = Math.sin(a) * r; // saat yönünde dönüşe uygun
            const dy = Math.cos(a) * r;
            return (
              <mesh position={[-1.175 + dx, driveY + dy, side * (z + 0.17)]} material={paint(C.metal, { roughness: 0.35 })} castShadow>
                <boxGeometry args={[1.95, 0.11, 0.06]} />
              </mesh>
            );
          })()}
          {/* çamurluklar */}
          <mesh position={[-1.18, 1.15, side * (z - 0.02)]} geometry={roundedBox(3.2, 0.12, 0.42, 0.06, 0.04)} material={orange} castShadow />
        </group>
      ))}

      {/* --- Kazan (yuvarlak ön bölüm) --- */}
      <mesh position={[1.05, boilerY, 0]} rotation={[0, 0, Math.PI / 2]} material={yellow} castShadow receiveShadow>
        <cylinderGeometry args={[0.95, 0.95, 3.1, 48]} />
      </mesh>
      {[0.35, 1.6].map((x) => (
        <mesh key={x} position={[x, boilerY, 0]} rotation={[0, Math.PI / 2, 0]} material={orange} castShadow>
          <torusGeometry args={[0.96, 0.06, 12, 48]} />
        </mesh>
      ))}
      {/* duman kutusu ve gülen yüz */}
      <mesh position={[2.72, boilerY, 0]} rotation={[0, 0, Math.PI / 2]} material={orange} castShadow>
        <cylinderGeometry args={[0.99, 0.99, 0.3, 48]} />
      </mesh>
      <group position={[2.88, boilerY, 0]}>
        <mesh rotation={[0, 0, Math.PI / 2]} scale={[1, 0.12, 1]} material={cream}>
          <sphereGeometry args={[0.86, 40, 20]} />
        </mesh>
        {[0.32, -0.32].map((zz) => (
          <group key={zz} position={[0.1, 0.22, zz]}>
            <mesh scale={[0.06, 0.15, 0.12]} material={dark}>
              <sphereGeometry args={[1, 20, 14]} />
            </mesh>
            <mesh position={[0.05, 0.06, -0.035]} scale={[0.02, 0.04, 0.035]} material={white}>
              <sphereGeometry args={[1, 10, 8]} />
            </mesh>
          </group>
        ))}
        {/* gülümseme */}
        <mesh position={[0.1, -0.08, 0]} rotation={[0, Math.PI / 2, Math.PI]} material={dark}>
          <torusGeometry args={[0.3, 0.045, 10, 32, Math.PI]} />
        </mesh>
        {[0.56, -0.56].map((zz) => (
          <mesh key={zz} position={[0.06, -0.06, zz]} scale={[0.03, 0.11, 0.15]} material={pink}>
            <sphereGeometry args={[1, 16, 12]} />
          </mesh>
        ))}
      </group>
      {/* ön lamba */}
      <mesh position={[2.7, boilerY + 1.0, 0]} material={paint('#FFF6C2', { emissive: '#FFE58A', emissiveIntensity: 0.6 })}>
        <sphereGeometry args={[0.16, 20, 16]} />
      </mesh>

      {/* --- Baca --- */}
      <mesh position={[LOCO.chimneyTop.x, 3.15, 0]} material={orange} castShadow>
        <cylinderGeometry args={[0.24, 0.26, 0.6, 28]} />
      </mesh>
      <mesh position={[LOCO.chimneyTop.x, 3.52, 0]} material={paint(C.red)} castShadow>
        <cylinderGeometry args={[0.36, 0.26, 0.24, 28]} />
      </mesh>
      {/* kubbe */}
      <mesh position={[0.7, 2.92, 0]} material={yellow} castShadow>
        <sphereGeometry args={[0.33, 28, 18]} />
      </mesh>
      <mesh position={[0.7, 3.22, 0]} material={orange}>
        <sphereGeometry args={[0.12, 16, 12]} />
      </mesh>

      {/* --- Kabin --- */}
      <group>
        {/* taban */}
        <mesh position={[-1.9, 1.15, 0]} geometry={roundedBox(2.8, 0.1, 2.2, 0.08, 0.03)} material={paint('#C98A4B')} receiveShadow />
        {/* alçak yan duvarlar (kapı eşiği) */}
        {[1, -1].map((s) => (
          <mesh key={s} position={[-1.9, 1.38, s * 1.08]} geometry={roundedBox(2.8, 0.46, 0.14, 0.06, 0.05)} material={yellow} castShadow receiveShadow />
        ))}
        {/* arka duvar */}
        <mesh position={[-3.23, 2.475, 0]} geometry={roundedBox(0.14, 2.65, 2.3, 0.06, 0.05)} material={yellow} castShadow receiveShadow />
        {/* arka yan paneller (yuvarlak pencereli) */}
        {[1, -1].map((s) => (
          <group key={s}>
            <mesh position={[-2.93, 2.635, s * 1.08]} geometry={roundedBox(0.75, 2.13, 0.14, 0.06, 0.05)} material={yellow} castShadow />
            <mesh position={[-2.93, 2.85, s * 1.16]} material={orange}>
              <torusGeometry args={[0.22, 0.055, 12, 32]} />
            </mesh>
            <mesh position={[-2.93, 2.85, s * 1.15]} material={glassMaterial()}>
              <circleGeometry args={[0.2, 32]} />
            </mesh>
            {/* ön dikme */}
            <mesh position={[-0.68, 2.635, s * 1.08]} geometry={roundedBox(0.2, 2.13, 0.16, 0.06, 0.05)} material={orange} castShadow />
            {/* açıklık çerçevesi alt kenarı */}
            <mesh position={[-1.78, 1.62, s * 1.1]} geometry={roundedBox(2.0, 0.08, 0.2, 0.03, 0.03)} material={orange} />
          </group>
        ))}
        {/* ön duvar: alt kısım dolu, üstte büyük ön cam */}
        <mesh position={[-0.6, 1.85, 0]} geometry={roundedBox(0.14, 1.4, 2.3, 0.06, 0.05)} material={yellow} castShadow />
        <mesh position={[-0.6, 3.1, 0]} material={glassMaterial()}>
          <boxGeometry args={[0.04, 1.1, 2.0]} />
        </mesh>
        <mesh position={[-0.6, 3.1, 0]} geometry={roundedBox(0.12, 0.1, 2.3, 0.04, 0.03)} material={orange} />
        {/* çatı: yuvarlatılmış, dışa taşan */}
        <mesh position={[-1.9, 3.81, 0]} geometry={roundedBox(3.25, 0.24, 2.75, 0.3, 0.1)} material={orange} castShadow receiveShadow />
        <mesh position={[-1.9, 3.95, 0]} scale={[1.55, 0.12, 1.25]} material={orange} castShadow>
          <sphereGeometry args={[1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        </mesh>
        {/* gösterge paneli */}
        <mesh position={[-1.0, 1.42, 0]} geometry={roundedBox(0.5, 0.55, 1.7, 0.08, 0.05)} material={chassis} castShadow />
        {[-0.45, 0, 0.45].map((zz, i) => (
          <mesh key={zz} position={[-1.24, 1.55, zz]} rotation={[0, 0, Math.PI / 2]} material={paint(['#FF5D5D', '#4CC36B', '#4D9BFF'][i])}>
            <cylinderGeometry args={[0.07, 0.07, 0.05, 16]} />
          </mesh>
        ))}
        {/* direksiyon */}
        <group position={LOCO.steeringWheel.toArray()} rotation={[0, 0, -0.7]}>
          <group rotation={[steeringTurn, 0, 0]}>
            <mesh rotation={[0, Math.PI / 2, 0]} material={paint(C.red)} castShadow>
              <torusGeometry args={[0.3, 0.045, 12, 36]} />
            </mesh>
            {[0, Math.PI / 2].map((r) => (
              <mesh key={r} rotation={[r, 0, 0]} material={paint(C.red)}>
                <boxGeometry args={[0.04, 0.56, 0.05]} />
              </mesh>
            ))}
            <mesh rotation={[0, 0, Math.PI / 2]} material={paint(C.locoYellow)}>
              <cylinderGeometry args={[0.09, 0.09, 0.07, 20]} />
            </mesh>
          </group>
          {/* direksiyon mili */}
          <mesh position={[0.28, 0, 0]} rotation={[0, 0, Math.PI / 2]} material={dark}>
            <cylinderGeometry args={[0.04, 0.04, 0.5, 12]} />
          </mesh>
        </group>
        {/* koltuk */}
        <mesh position={[-2.55, 1.22, 0]} geometry={roundedBox(0.8, 0.18, 1.5, 0.08, 0.06)} material={paint(C.red)} castShadow />
        <mesh position={[-3.02, 1.75, 0]} geometry={roundedBox(0.22, 0.95, 1.5, 0.1, 0.08)} material={paint(C.red)} castShadow />
        {/* kabin içi yumuşak dolgu ışığı: çatı gölgesinde sürücünün yüzü kararmasın */}
        <pointLight position={[-1.3, 3.0, 0.9]} intensity={9} distance={5} decay={2} color="#FFF4E0" />
        {children}
      </group>
    </group>
  );
};
