import type React from 'react';
import type { SceneProps } from './types';
import { Scene01 } from './Scene01';
import { Scene02 } from './Scene02';
import { PendingScene } from './PendingScene';

/**
 * Sahne kimliği → bileşen. Bir sahneyi değiştirmek yalnızca kendi dosyasını etkiler.
 * Listede olmayan sahneler açıkça "yapım aşamasında" kartı gösterir.
 */
export const SCENE_COMPONENTS: Record<string, React.FC<SceneProps>> = {
  s01: Scene01,
  s02: Scene02,
};

export const isImplemented = (id: string) => id in SCENE_COMPONENTS;
export const sceneComponent = (id: string): React.FC<SceneProps> => SCENE_COMPONENTS[id] ?? PendingScene;
