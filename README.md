# FCP - Combat Extended Patch

Makes the Fallout Collaboration Project (FCP) mods work with Combat Extended (CE).

## Load order
Harmony, Core, DLCs, Combat Extended, all FCP mods, then this mod. Do not remove this mod from a save that has FCP + CE active.

## What is covered (phase 1: default CE ammo only)
| Area | FCP mods | What changes |
|---|---|---|
| Guns (157) | Ballistic, Energy, Explosive launchers, BoS, Enclave, NCR, Children of Atom | `Verb_ShootCE`, CE ammo set, magazine, reload, burst, range, recoil/spread/sway, bulk, CE AI tags. FCP-only verbs (`Verb_Shoot_Shotgunz`, `Verb_SpewFire`) are removed. |
| Grenades (22) | Explosive | `Verb_ShootCEOneUse`, explosive projectiles become `ProjectileCE_Explosive`; frag grenades get CE fragments. |
| Melee/unarmed/gun-bash tools | Melee, Unarmed, all guns | `ToolCE` with armor penetration. |
| Apparel (~280) incl. power armor | Tools, Power Armor, BoS, Enclave, NCR, Legion, Raiders, Wastelanders, Khans, Marked Men, Followers, CoA | CE armor values (mm RHA / MPa), `Bulk`, `WornBulk`. |
| Animals | Animals | CE armor values and `ToolCE` attacks. |

Patches live in `Patches/<FCP mod>/`; every operation carries `MayRequire` for its FCP mod, so it only applies when that mod is active. There is deliberately no `LoadFolders.xml`.

## Ammo mapping
See `Tools/caliber_map.py`. Examples: 10mm -> 10mm Auto, 5.56/.223 -> 5.56x45, 5mm -> 5.45x39, .308/7.62 -> 7.62x51, 12.7mm -> 12.7x55, 14mm -> .454 Casull, plasma -> CE plasma cells, laser -> CE charged ammo, gauss -> CE railgun ammo, flamers -> CE flamethrower fuel, rockets/Fatman -> CE rocket/recoilless ammo.

## Regenerating
`python FCP-Combat-Extended-Patch\Tools\generate.py` from the `Mods` folder. It rewrites `Patches/` from the FCP defs. Per-class weapon stats are in `generate.py`, ammo in `caliber_map.py`.

## Phase 2 (not done yet)
Fallout specific CE ammo (10mm, 5mm, .44, 2mm EC, fusion cells, ...): add the AmmoSet/ammo defs and point the entries in `caliber_map.py` at them.

## Known limitations
- Beam/laser visuals, Fatman mini-nuke and similar unique FCP projectiles are replaced by the CE projectile of the mapped ammo.
- FCP weapon jam/condition logic only hooks `Verb_Shoot`, so it does not trigger on CE guns.
- Custom animal body (lurker) and trader/pawnkind ammo stock are not tuned for CE; CE still generates ammo for NPCs from their weapon.
