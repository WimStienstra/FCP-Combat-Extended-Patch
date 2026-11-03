"""Caliber map: FCP projectile -> Combat Extended AmmoSet.

Phase 1 uses only ammo that ships with Combat Extended. To introduce Fallout specific
ammo later (phase 2), add the new AmmoSet defs and change the entries below.
"""
import re

AMMO_BY_PROJECTILE = {
    # Ballistic
    'FCP_Bullet_9mm': 'AmmoSet_9x19mmPara',
    'FCP_Bullet_10mm': 'AmmoSet_10mmAuto',
    'FCP_Bullet_127mm': 'AmmoSet_127x55mm',
    'FCP_Bullet_14mm': 'AmmoSet_454Casull',
    'FCP_Bullet_22LR': 'AmmoSet_22LR',
    'FCP_Bullet_223mm': 'AmmoSet_556x45mmNATO',
    'FCP_Bullet_556mm': 'AmmoSet_556x45mmNATO',
    'FCP_Bullet_5mm': 'AmmoSet_545x39mmSoviet',
    'FCP_Bullet_32mm': 'AmmoSet_32ACP',
    'FCP_Bullet_357mm': 'AmmoSet_357Magnum',
    'FCP_Bullet_44Magnum': 'AmmoSet_44Magnum',
    'FCP_Bullet_4570mm': 'AmmoSet_4570Gov',
    'FCP_Bullet_45ACP': 'AmmoSet_45ACP',
    'FCP_Bullet_50AE': 'AmmoSet_50AE',
    'FCP_Bullet_50Cal': 'AmmoSet_50BMG',
    'FCP_Bullet_308mm': 'AmmoSet_762x51mmNATO',
    'FCP_Bullet_762mm': 'AmmoSet_762x51mmNATO',
    'FCP_Bullet_BB': 'AmmoSet_22Short',
    'FCP_Bullet_Nail': 'AmmoSet_Nail',
    'FCP_Bullet_12Gauge_Pellet': 'AmmoSet_12Gauge',
    'FCP_Bullet_20Gauge_Pellet': 'AmmoSet_20Gauge',
    'FCP_Bullet_Shotgun': 'AmmoSet_12Gauge',
    'FCP_Bullet_Ranger_Ricks_Big_Iron_Revolver': 'AmmoSet_357Magnum',
    'FCP_Bullet_Ranger_Sequoia': 'AmmoSet_4570Gov',
    'FCP_Bullet_Autocannon': 'AmmoSet_Autocannon',
    # Explosive launchers
    'FCP_Proj_Grenade_Fragmentation': 'AmmoSet_40x46mmGrenade',
    'FCP_Bullet_MiniNuke': 'AmmoSet_90mmRecoilless',
    'Bullet_Rocket': 'AmmoSet_83mmSMAW',
    # Energy
    'FCP_Beam_Laser': 'AmmoSet_6x24mmCharged',
    'FCP_Beam_Laser_S': 'AmmoSet_6x24mmCharged',
    'FCP_Beam_Gatling_Laser': 'AmmoSet_8x35mmCharged',
    'FCP_Beam_MF_Breeder': 'AmmoSet_5x16mmCharged',
    'FCP_Bullet_Plasma': 'AmmoSet_PlasmaCellRifle',
    'FCP_Bullet_Plasma_Cannon': 'AmmoSet_PlasmaCellHeavy',
    'FCP_Bullet_Ultracite': 'AmmoSet_PlasmaCellRifle',
    'FCP_Bullet_Gamma': 'AmmoSet_PlasmaCellPistol',
    'FCP_Bullet_Gamma_Heavy': 'AmmoSet_PlasmaCellRifle',
    'FCP_Bullet_Gauss': 'AmmoSet_8mmRailgun',
    'Bullet_EMPLauncher': 'AmmoSet_40x46mmOnlyEMP',
}

# Per weapon overrides (exact defName). Keep this small; use for lore / balance exceptions.
AMMO_OVERRIDES_BY_DEF = {
    'FCP_Gun_Grenade_Machinegun': 'AmmoSet_40x53mmGrenade',
    'FCP_Gun_25MM_Grenade_Launcher': 'AmmoSet_25x40mmGrenade',
    'FCP_Gun_Broadsider': 'AmmoSet_90mmRecoilless',
    'FCP_Gun_Red_Glare': 'AmmoSet_80mmRocket_direct',
    'FCP_Gun_Rockwell_Big_Bazooka': 'AmmoSet_88mmRPzBRocket',
    'FCP_Gun_YK32_Pulse_Pistol': 'AmmoSet_40x46mmOnlyEMP',
    'FCP_Gun_YK42B_Pulse_Rifle': 'AmmoSet_40x46mmOnlyEMP',
    # long range 32 cal rifles use a rifle round instead of a pistol round
    'FCP_Gun_32_Hunting_Rifle': 'AmmoSet_3030Winchester',
    'FCP_Gun_OlPainless': 'AmmoSet_3030Winchester',
    'FCP_Gun_Pipe_Rifle': 'AmmoSet_3030Winchester',
    # smaller plasma / laser / gauss frames
    'FCP_Gun_Plasma_Pistol': 'AmmoSet_PlasmaCellPistol',
    'FCP_Gun_Glock_86_Plasma_Pistol': 'AmmoSet_PlasmaCellPistol',
    'FCP_Gun_Plasma_Defender': 'AmmoSet_PlasmaCellPistol',
    'FCP_Gun_Enclave_Plasma_SMG': 'AmmoSet_PlasmaCellPistol',
    'FCP_Gun_Plasma_Machine_Gun': 'AmmoSet_PlasmaCellHeavy',
    'FCP_Gun_Plasma_Caster': 'AmmoSet_PlasmaCellHeavy',
    'FCP_Gun_Plasma_Caster_MkI': 'AmmoSet_PlasmaCellHeavy',
    'FCP_Gun_Laser_Pistol': 'AmmoSet_5x16mmCharged',
    'FCP_Gun_Wattz_1000_Laser_Pistol': 'AmmoSet_5x16mmCharged',
    'FCP_Gun_AER14_Prototype': 'AmmoSet_6x24mmCharged',
    'FCP_Gun_PPK12_Gauss_Pistol': 'AmmoSet_6mmRailgun',
    'FCP_Gun_Gauss_Sniper_Rifle': 'AmmoSet_12mmRailgun',
    'FCP_Gun_Gauss_Minigun': 'AmmoSet_12mmRailgun',
    'FCP_Gun_Sprtel_Wood_9700_Unique': 'AmmoSet_8x35mmCharged',
}

# Regex fallbacks applied when no exact override matches (defName pattern -> ammo set)
AMMO_PATTERNS = [
    (re.compile(r'Pistol$', re.I), {'AmmoSet_PlasmaCellRifle': 'AmmoSet_PlasmaCellPistol',
                                    'AmmoSet_8mmRailgun': 'AmmoSet_6mmRailgun',
                                    'AmmoSet_6x24mmCharged': 'AmmoSet_5x16mmCharged'}),
]


def ammo_for(def_name, projectile, is_flamer=False):
    if is_flamer:
        return 'AmmoSet_Flamethrower'
    if def_name in AMMO_OVERRIDES_BY_DEF:
        return AMMO_OVERRIDES_BY_DEF[def_name]
    ammo = AMMO_BY_PROJECTILE.get(projectile)
    if ammo is None:
        return None
    for pat, sub in AMMO_PATTERNS:
        if pat.search(def_name) and ammo in sub:
            return sub[ammo]
    return ammo
