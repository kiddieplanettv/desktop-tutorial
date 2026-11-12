3D karakterler (büyük olduğu için depoda değil). Yeniden üretmek için:

1. Hunyuan3D-2mv ile şekil: `hymv.py <ad> v0 v4 <sol> <sağ> <çıktı> /shape_generation` (ön/arka/yan görünüşler `chars2/<ad>/`).
2. Boyama + iskelet: `blender -b -P rig3d.py -- <ad> <şekil.glb> <boy_m> v0 v4 <+X görünüş> <-X görünüş>`
