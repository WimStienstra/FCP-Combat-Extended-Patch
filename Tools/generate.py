"""Generates the Combat Extended patches for the FCP mods.

Run from the Mods folder:  python FCP-Combat-Extended-Patch\\Tools\\generate.py
Output: FCP-Combat-Extended-Patch\\Modules\\<FCP mod folder>\\Patches\\*.xml and LoadFolders.xml

All tuning lives in caliber_map.py (ammo sets) and in the tables below (per weapon class stats).
"""
import glob
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from caliber_map import ammo_for  # noqa: E402

MODS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(MODS, 'FCP-Combat-Extended-Patch')
CE = r'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2890901044'


def f2(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return s or '0'


# ---------------------------------------------------------------- loading
def mod_packages():
    res = {}
    for d in sorted(glob.glob(os.path.join(MODS, 'FCP-*'))):
        name = os.path.basename(d)
        about = os.path.join(d, 'About', 'About.xml')
        if name == 'FCP-Combat-Extended-Patch' or not os.path.exists(about):
            continue
        pid = ET.parse(about).getroot().findtext('packageId')
        res[name] = pid
    return res


def load_defs(modname):
    """Returns list of (file, ThingDef element) for a mod (all Defs folders)."""
    out = []
    base = os.path.join(MODS, modname)
    for f in glob.glob(os.path.join(base, '**', 'Defs', '**', '*.xml'), recursive=True):
        if '\\Source\\' in f or '\\FCP-UnityAssets\\' in f:
            continue
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        for d in root.findall('ThingDef'):
            out.append((f, d))
    return out


def load_ammo_sets():
    """AmmoSet defName -> default (first) projectile defName."""
    sets = {}
    for f in glob.glob(os.path.join(CE, 'Defs', 'Ammo', '**', '*.xml'), recursive=True):
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        for d in root:
            if d.tag.endswith('AmmoSetDef') or d.get('Class', '').endswith('AmmoSetDef') or d.tag == 'CombatExtended.AmmoSetDef':
                dn = d.findtext('defName')
                at = d.find('ammoTypes')
                if dn and at is not None and len(at):
                    sets[dn] = at[0].text.strip()
    return sets


ALL = {}      # key -> (modname, file, element)
for _mod in mod_packages():
    for _f, _d in load_defs(_mod):
        for _k in (_d.findtext('defName'), '@' + _d.get('Name', '') if _d.get('Name') else None):
            if _k:
                ALL[_k] = (_mod, _f, _d)


def parent_chain(d):
    chain = []
    seen = set()
    while d is not None:
        pn = d.get('ParentName')
        if not pn or pn in seen:
            break
        seen.add(pn)
        e = ALL.get('@' + pn)
        if not e:
            break
        d = e[2]
        chain.append(d)
    return chain


def inherited(d, path):
    """First element found for path walking up the FCP parent chain."""
    for x in [d] + parent_chain(d):
        e = x.find(path)
        if e is not None:
            return e
    return None


def inherited_text(d, path):
    e = inherited(d, path)
    return e.text.strip() if e is not None and e.text else None


def selector(d):
    dn = d.findtext('defName')
    if dn:
        return 'Defs/ThingDef[defName="%s"]' % dn
    return 'Defs/ThingDef[@Name="%s"]' % d.get('Name')


def may_require(d):
    mr = d.get('MayRequire')
    return ' MayRequire="%s"' % mr if mr else ''


def num(e, default=None):
    try:
        return float(e.text)
    except (AttributeError, TypeError, ValueError):
        return default


# ---------------------------------------------------------------- guns
CLASS_STATS = {
    # recoil, spread, sway, sights, rangeMul, mag, reload, aim, tags, cooldownMul, ai, bulkMul
    'revolver': dict(recoil=2.9, spread=0.16, sway=1.35, sights=0.7, rng=0.85, mag=6, reload=4.6, aim='Snapshot',
                     tags=['CE_Sidearm', 'CE_AI_BROOM', 'CE_OneHandedWeapon'], cd=0.5),
    'pistol': dict(recoil=2.5, spread=0.17, sway=1.1, sights=0.7, rng=0.85, mag=12, reload=4.0, aim='Snapshot',
                   tags=['CE_Sidearm', 'CE_AI_BROOM', 'CE_OneHandedWeapon'], cd=0.4),
    'smg': dict(recoil=1.75, spread=0.12, sway=1.0, sights=0.8, rng=1.1, mag=30, reload=4.0, aim='Snapshot',
                tags=['CE_SMG', 'CE_AI_BROOM'], cd=0.6),
    'rifle': dict(recoil=1.8, spread=0.1, sway=0.9, sights=1.0, rng=1.8, mag=30, reload=4.0, aim='AimedShot',
                  tags=['CE_AI_AR', 'CE_AI_Rifle'], cd=0.8),
    'boltrifle': dict(recoil=2.0, spread=0.07, sway=0.8, sights=1.1, rng=1.9, mag=8, reload=4.0, aim='AimedShot',
                      tags=['CE_AI_Rifle'], cd=1.0),
    'sniper': dict(recoil=1.7, spread=0.04, sway=0.7, sights=1.4, rng=2.0, mag=5, reload=4.2, aim='AimedShot',
                   tags=['CE_AI_SR'], cd=1.1),
    'shotgun': dict(recoil=2.7, spread=0.14, sway=1.1, sights=0.8, rng=1.0, mag=6, reload=5.0, aim='Snapshot',
                    tags=['CE_AI_BROOM'], cd=0.9),
    'lmg': dict(recoil=1.4, spread=0.1, sway=1.3, sights=0.9, rng=1.8, mag=100, reload=7.0, aim='SuppressFire',
                tags=['CE_AI_LMG', 'CE_AI_Suppressive', 'CE_MachineGun'], cd=0.9),
    'heavy': dict(recoil=1.0, spread=0.1, sway=1.7, sights=0.8, rng=1.5, mag=250, reload=9.0, aim='SuppressFire',
                  tags=['CE_AI_LMG', 'CE_AI_Suppressive', 'CE_MachineGun'], cd=1.0),
    'launcher': dict(recoil=3.8, spread=0.1, sway=1.4, sights=0.8, rng=1.5, mag=1, reload=5.0, aim='AimedShot',
                     tags=['CE_AI_Launcher', 'CE_AI_AOE'], cd=1.2),
    'energy_pistol': dict(recoil=1.0, spread=0.15, sway=1.1, sights=0.7, rng=1.0, mag=20, reload=3.5, aim='Snapshot',
                          tags=['CE_Sidearm', 'CE_AI_BROOM', 'CE_OneHandedWeapon'], cd=0.5),
    'flamer': dict(recoil=0.5, spread=0.1, sway=1.5, sights=0.7, rng=1.0, mag=25, reload=6.0, aim='SuppressFire',
                   tags=['CE_AI_AOE', 'CE_AI_Suppressive'], cd=1.2),
}

GRENADE_TAGS = ['CE_AI_Grenade', 'CE_AI_AOE', 'CE_OneHandedWeapon']


def classify(name, d, ammo_set, burst, mass, rng):
    n = name.lower()
    if ammo_set == 'AmmoSet_Flamethrower':
        return 'flamer'
    launcher_sets = ('Rocket', 'SMAW', 'Recoilless', 'Grenade', 'Autocannon', 'AmmoSet_Flare', 'PIAT')
    if any(x in ammo_set for x in launcher_sets):
        if burst >= 4 and 'Grenade' in ammo_set:
            return 'heavy'
        if ammo_set == 'AmmoSet_Autocannon':
            return 'heavy'
        return 'launcher'
    if 'Charged' in ammo_set or 'Plasma' in ammo_set or 'Railgun' in ammo_set or 'EMP' in ammo_set:
        if 'pistol' in n or (mass <= 3.0 and rng <= 23 and burst <= 3):
            return 'energy_pistol'
        if burst >= 8 and mass >= 6:
            return 'heavy' if mass >= 8 else 'lmg'
        if burst >= 3 and mass <= 4.5 and rng <= 24:
            return 'smg'
        if rng >= 38 and burst <= 1:
            return 'sniper'
        return 'rifle'
    if 'Gauge' in ammo_set or 'Shotgun' in ammo_set:
        return 'shotgun'
    if burst <= 1 and rng >= 38 and mass >= 5:
        return 'sniper'
    if burst >= 20 or mass >= 11:
        return 'heavy'
    if (burst >= 10 and mass >= 6) or (mass >= 7 and burst > 1):
        return 'lmg'
    if 'revolver' in n or ('repeater' in n and mass < 3.5):
        return 'revolver'
    if burst >= 3 and mass <= 4.5 and rng <= 24:
        return 'smg'
    if burst <= 1 and mass <= 2.9 and rng <= 24 and 'rifle' not in n:
        return 'pistol'
    if burst <= 1 and rng >= 38:
        return 'sniper'
    if burst <= 1 and rng >= 26:
        return 'boltrifle'
    if burst <= 1 and mass <= 3.2:
        return 'pistol'
    return 'rifle'


def verb_info(d):
    """Own verbs (list of elements); falls back to inherited verbs."""
    v = d.findall('verbs/li')
    if v:
        return v
    for p in parent_chain(d):
        v = p.findall('verbs/li')
        if v:
            return v
    return []


def is_grenade(d):
    for li in verb_info(d):
        if 'LaunchProjectileConsumable' in (li.findtext('verbClass') or '') or 'LaunchProjectile' == li.findtext('verbClass'):
            return True
    return False


def gun_patch(d, ammo_sets, report):
    dn = d.findtext('defName')
    verbs = verb_info(d)
    if not verbs:
        return None
    v = verbs[0]
    vc = v.findtext('verbClass') or ''
    proj = v.findtext('defaultProjectile') or ''
    own_verbs = d.findall('verbs/li')

    ammo = ammo_for(dn, proj, 'SpewFire' in vc)
    if not ammo:
        report.append('NO AMMO MAP: %s (%s)' % (dn, proj))
        return None
    if ammo not in ammo_sets:
        report.append('UNKNOWN AMMO SET %s for %s' % (ammo, dn))
        return None
    cproj = ammo_sets[ammo]

    mass = num(inherited(d, 'statBases/Mass'), 3.0)
    fcp_cd = num(inherited(d, 'statBases/RangedWeapon_Cooldown'), 1.0)
    burst = int(num(v.find('burstShotCount'), 1) or 1)
    ticks = int(num(v.find('ticksBetweenBurstShots'), 0) or 0)
    rng = num(v.find('range'), 20)
    warm = num(v.find('warmupTime'), 1.0)
    pellets = int(num(v.find('pellets'), 1) or 1)
    cls = classify(dn, d, ammo, burst, mass, rng)
    c = CLASS_STATS[cls]

    # (stats are CE-flavoured but derived from the original FCP numbers)
    bulk = max(1.0, round(mass * 2.1, 2)) if cls not in ('heavy', 'launcher') else round(mass * 1.6, 2)
    cooldown = max(0.3, round(min(fcp_cd, 3.0) * c['cd'], 2)) if burst > 1 or cls in ('launcher', 'heavy') else c['cd']
    if cls in ('sniper', 'boltrifle'):
        cooldown = max(cooldown, round(fcp_cd * 0.65, 2))
    cd_tag = f2(cooldown)

    rng_ce = max(8, round(rng * c['rng']))
    warm_ce = f2(max(0.4, warm if cls not in ('pistol', 'revolver', 'energy_pistol') else max(0.5, warm)))
    mag = c['mag']
    if cls == 'rifle' and burst >= 12:
        mag = 40
    if cls == 'smg' and burst >= 8:
        mag = 40
    if cls == 'heavy' and mass < 11:
        mag = 100
    if burst <= 1 and cls == 'heavy':
        mag = 20
    if ammo == 'AmmoSet_Autocannon':
        mag = 30
    if cls == 'rifle' and burst >= 10:
        mag = 50
    if cls == 'sniper' and ('Railgun' in ammo or 'Plasma' in ammo):
        mag = 10
    if cls == 'rifle' and 'PlasmaCellHeavy' in ammo:
        mag = 20
    if cls == 'rifle' and (burst <= 3 and ('Charged' in ammo or 'Plasma' in ammo)):
        mag = 24
    if cls == 'launcher':
        mag = 1 if burst <= 1 else burst
    if cls == 'shotgun':
        mag = 6 if mass < 4.5 else 8
        if 'sawn' in dn.lower() or 'single' in dn.lower() or 'dinner' in dn.lower() or 'wanda' in dn.lower():
            mag = 2
        if 'jackhammer' in dn.lower() or 'riot' in dn.lower() or 'combat' in dn.lower():
            mag = 12
    if cls == 'pistol' and ('deagle' in dn.lower() or '127' in dn or '14mm' in dn.lower()):
        mag = 8
    if cls == 'revolver' and 'repeater' in dn.lower():
        mag = 10
    if cls == 'sniper' and 'anti_material' in dn.lower():
        mag = 5
    if ammo == 'AmmoSet_Flamethrower':
        mag = 25

    use_burst = burst > 1 or cls in ('lmg', 'heavy')
    burst_ce = burst
    if cls == 'launcher':
        burst_ce = 1 if burst <= 1 else burst
    if cls == 'shotgun':
        burst_ce = 1
    if cls == 'flamer':
        burst_ce = 1

    sound = v.findtext('soundCast')
    tail = v.findtext('soundCastTail') or 'GunTail_Light'
    flash = v.findtext('muzzleFlashScale') or '9'

    out = []
    out.append('\t<Operation Class="CombatExtended.PatchOperationMakeGunCECompatible"%s>' % may_require(d))
    out.append('\t\t<defName>%s</defName>' % dn)
    out.append('\t\t<statBases>')
    out.append('\t\t\t<Bulk>%s</Bulk>' % f2(bulk))
    out.append('\t\t\t<RangedWeapon_Cooldown>%s</RangedWeapon_Cooldown>' % cd_tag)
    out.append('\t\t\t<SightsEfficiency>%s</SightsEfficiency>' % f2(c['sights']))
    out.append('\t\t\t<ShotSpread>%s</ShotSpread>' % f2(c['spread']))
    out.append('\t\t\t<SwayFactor>%s</SwayFactor>' % f2(c['sway']))
    out.append('\t\t</statBases>')
    out.append('\t\t<Properties>')
    out.append('\t\t\t<recoilAmount>%s</recoilAmount>' % f2(c['recoil']))
    out.append('\t\t\t<verbClass>CombatExtended.Verb_ShootCE</verbClass>')
    out.append('\t\t\t<hasStandardCommand>true</hasStandardCommand>')
    out.append('\t\t\t<defaultProjectile>%s</defaultProjectile>' % cproj)
    out.append('\t\t\t<warmupTime>%s</warmupTime>' % warm_ce)
    out.append('\t\t\t<range>%d</range>' % rng_ce)
    if burst_ce > 1:
        out.append('\t\t\t<burstShotCount>%d</burstShotCount>' % burst_ce)
        out.append('\t\t\t<ticksBetweenBurstShots>%d</ticksBetweenBurstShots>' % (ticks if ticks > 0 else 5))
    if sound:
        out.append('\t\t\t<soundCast>%s</soundCast>' % sound)
    out.append('\t\t\t<soundCastTail>%s</soundCastTail>' % tail)
    out.append('\t\t\t<muzzleFlashScale>%s</muzzleFlashScale>' % flash)
    out.append('\t\t</Properties>')
    out.append('\t\t<AmmoUser>')
    out.append('\t\t\t<magazineSize>%d</magazineSize>' % mag)
    out.append('\t\t\t<reloadTime>%s</reloadTime>' % f2(c['reload']))
    out.append('\t\t\t<ammoSet>%s</ammoSet>' % ammo)
    out.append('\t\t</AmmoUser>')
    out.append('\t\t<FireModes>')
    out.append('\t\t\t<aiUseBurstMode>%s</aiUseBurstMode>' % ('TRUE' if use_burst else 'FALSE'))
    if burst_ce >= 4:
        out.append('\t\t\t<aimedBurstShotCount>%d</aimedBurstShotCount>' % max(2, burst_ce // 2))
    elif burst_ce > 1:
        out.append('\t\t\t<aimedBurstShotCount>%d</aimedBurstShotCount>' % max(1, burst_ce - 1))
    out.append('\t\t\t<aiAimMode>%s</aiAimMode>' % c['aim'])
    out.append('\t\t</FireModes>')
    out.append('\t\t<weaponTags>')
    for t in c['tags']:
        out.append('\t\t\t<li>%s</li>' % t)
    out.append('\t\t</weaponTags>')
    out.append('\t</Operation>')

    pre = []
    # the CE operation only removes plain Verb_Shoot / Verb_LaunchProjectile; drop the FCP specific verbs ourselves
    for li in own_verbs:
        vclass = li.findtext('verbClass') or ''
        if vclass not in ('Verb_Shoot', 'Verb_ShootOneUse', 'Verb_LaunchProjectile'):
            pre.append('\t<Operation Class="PatchOperationRemove"%s>\n\t\t<xpath>%s/verbs/li[verbClass="%s"]</xpath>\n\t</Operation>'
                       % (may_require(d), selector(d), vclass))
    # a def with no own verbs inheriting them: nothing to remove, CE verb gets added to the child.
    report.append('GUN %-45s %-9s %-26s mag=%d burst=%d' % (dn, cls, ammo, mag, burst_ce))
    return '\n'.join(pre + out)


# ---------------------------------------------------------------- tools (melee)
def tool_ce(li, parent_desc=''):
    """Converts a <li> Tool to ToolCE (serialised string, tab indented)."""
    caps = [c.text for c in li.findall('capacities/li')]
    power = num(li.find('power'), 0) or 0
    cut = any(c in ('Cut',) for c in caps)
    stab = any(c in ('Stab', 'Poke') for c in caps)
    claw = any(c in ('Scratch', 'Bite') for c in caps)
    blunt = any(c in ('Blunt',) for c in caps)
    if cut:
        sharp = power / 18.0
    elif stab:
        sharp = power / 11.0
    elif claw:
        sharp = power / 14.0
    else:
        sharp = 0.0
    bl = power * (0.33 if blunt else 0.12)

    lines = ['\t\t\t\t<li Class="CombatExtended.ToolCE">']
    existing = {c.tag for c in li}
    for child in li:
        if child.tag in ('armorPenetrationSharp', 'armorPenetrationBlunt'):
            continue
        child_s = ET.tostring(child, encoding='unicode').strip()
        child_s = re.sub(r'\s*\n\s*', ' ', child_s)
        child_s = re.sub(r'>\s+<', '><', child_s)
        lines.append('\t\t\t\t\t' + child_s)
    if sharp > 0:
        lines.append('\t\t\t\t\t<armorPenetrationSharp>%s</armorPenetrationSharp>' % f2(round(sharp, 3)))
    lines.append('\t\t\t\t\t<armorPenetrationBlunt>%s</armorPenetrationBlunt>' % f2(round(bl, 3)))
    lines.append('\t\t\t\t</li>')
    return '\n'.join(lines)


def tools_patch(d):
    lis = d.findall('tools/li')
    if not lis:
        return None
    body = '\n'.join(tool_ce(li) for li in lis)
    return ('\t<Operation Class="PatchOperationReplace"%s>\n\t\t<xpath>%s/tools</xpath>\n\t\t<value>\n\t\t\t<tools>\n%s\n\t\t\t</tools>\n\t\t</value>\n\t</Operation>'
            % (may_require(d), selector(d), body))


def melee_bulk_patch(d):
    """CE needs a Bulk stat on every weapon."""
    mass = num(inherited(d, 'statBases/Mass'), 1.5)
    bulk = max(1.0, round(mass * 1.5, 2))
    return ('\t<Operation Class="PatchOperationConditional"%s>\n\t\t<xpath>%s/statBases</xpath>\n'
            '\t\t<match Class="PatchOperationAdd">\n\t\t\t<xpath>%s/statBases</xpath>\n\t\t\t<value><Bulk>%s</Bulk></value>\n\t\t</match>\n'
            '\t\t<nomatch Class="PatchOperationAdd">\n\t\t\t<xpath>%s</xpath>\n\t\t\t<value><statBases><Bulk>%s</Bulk></statBases></value>\n\t\t</nomatch>\n\t</Operation>'
            % (may_require(d), selector(d), selector(d), f2(bulk), selector(d), f2(bulk)))


# ---------------------------------------------------------------- apparel
POWER_RE = re.compile(r'power_armor|t45|t51|t60|x-?01|hellfire|ultracite|salvaged', re.I)


def _curve(v, lo_mul, mid_step, hi_step):
    if v <= 1:
        return lo_mul * v
    if v <= 2:
        return lo_mul + mid_step * (v - 1)
    return lo_mul + mid_step + hi_step * (v - 2)


def armor_ce(sharp, blunt):
    """Vanilla 0..1 ratings -> CE mm RHA (sharp) / MPa (blunt). Values above 1 (power armor) are compressed."""
    return round(_curve(sharp, 10, 8, 5), 1), round(_curve(blunt, 20, 15, 10), 1)


def apparel_patch(d):
    ap = d.find('apparel')
    if ap is None:
        return None
    sb = d.find('statBases')
    ops = []
    sel = selector(d)
    mr = may_require(d)
    name = d.findtext('defName') or d.get('Name') or ''
    groups = [g.text for g in ap.findall('bodyPartGroups/li')]
    layers = [g.text for g in ap.findall('layers/li')]
    mass = num(inherited(d, 'statBases/Mass'), 1.0)
    sharp = num(sb.find('ArmorRating_Sharp')) if sb is not None else None
    blunt = num(sb.find('ArmorRating_Blunt')) if sb is not None else None
    heavy = bool(POWER_RE.search(name))
    head = any(g in ('UpperHead', 'FullHead', 'Eyes') for g in groups)
    torso = 'Torso' in groups

    # Bulk is only given to nodes that define Mass or armor themselves (children inherit the rest)
    own_stats = sb is not None
    if not own_stats and ap is None:
        return None
    if own_stats or d.find('apparel') is not None:
        if heavy and head:
            bulk, worn = 6, 2
        elif heavy:
            bulk, worn = 40, 15
        elif head:
            bulk, worn = 3 + (sharp or 0) * 3, 1
        elif torso and (sharp or 0) >= 0.2:
            bulk, worn = 5 + 6 * (sharp or 0), 2 + 3 * (sharp or 0)
        elif torso:
            bulk, worn = 3 + mass * 0.5, 1
        else:
            bulk, worn = 1 + mass * 0.4, 0.5
        bulk, worn = round(bulk, 1), round(worn, 1)
        # Give Bulk to the node only if it is a leaf definition or defines its own statBases
        if own_stats:
            ops.append('\t<Operation Class="PatchOperationAdd"%s>\n\t\t<xpath>%s/statBases</xpath>\n\t\t<value>\n'
                       '\t\t\t<Bulk>%s</Bulk>\n\t\t\t<WornBulk>%s</WornBulk>\n\t\t</value>\n\t</Operation>' % (mr, sel, f2(bulk), f2(worn)))
        else:
            ops.append('\t<Operation Class="PatchOperationAdd"%s>\n\t\t<xpath>%s</xpath>\n\t\t<value>\n\t\t\t<statBases>\n'
                       '\t\t\t\t<Bulk>%s</Bulk>\n\t\t\t\t<WornBulk>%s</WornBulk>\n\t\t\t</statBases>\n\t\t</value>\n\t</Operation>'
                       % (mr, sel, f2(bulk), f2(worn)))
    if sb is not None:
        if sharp is not None:
            s, _ = armor_ce(sharp, 0)
            ops.append('\t<Operation Class="PatchOperationReplace"%s>\n\t\t<xpath>%s/statBases/ArmorRating_Sharp</xpath>\n\t\t<value>\n'
                       '\t\t\t<ArmorRating_Sharp>%s</ArmorRating_Sharp>\n\t\t</value>\n\t</Operation>' % (mr, sel, f2(s)))
        if blunt is not None:
            _, b = armor_ce(0, blunt)
            ops.append('\t<Operation Class="PatchOperationReplace"%s>\n\t\t<xpath>%s/statBases/ArmorRating_Blunt</xpath>\n\t\t<value>\n'
                       '\t\t\t<ArmorRating_Blunt>%s</ArmorRating_Blunt>\n\t\t</value>\n\t</Operation>' % (mr, sel, f2(b)))
    return '\n'.join(ops)


# ---------------------------------------------------------------- animals / races
def race_patch(d):
    sb = d.find('statBases')
    ops = []
    sel = selector(d)
    mr = may_require(d)
    if sb is not None:
        for stat in ('ArmorRating_Sharp', 'ArmorRating_Blunt'):
            e = sb.find(stat)
            if e is not None and num(e) is not None:
                v = num(e)
                nv = armor_ce(v, 0)[0] if stat.endswith('Sharp') else armor_ce(0, v)[1]
                ops.append('\t<Operation Class="PatchOperationReplace"%s>\n\t\t<xpath>%s/statBases/%s</xpath>\n\t\t<value>\n\t\t\t<%s>%s</%s>\n\t\t</value>\n\t</Operation>'
                           % (mr, sel, stat, stat, f2(nv), stat))
    return '\n'.join(ops)


# ---------------------------------------------------------------- grenades / projectiles
def grenade_projectile_patch(d):
    sel = selector(d)
    mr = may_require(d)
    pr = d.find('projectile')
    ops = []
    ops.append('\t<Operation Class="PatchOperationAttributeSet"%s>\n\t\t<xpath>%s/projectile</xpath>\n\t\t<attribute>Class</attribute>\n\t\t<value>CombatExtended.ProjectilePropertiesCE</value>\n\t</Operation>' % (mr, sel))
    tc = d.find('thingClass')
    if tc is not None:
        ops.append('\t<Operation Class="PatchOperationReplace"%s>\n\t\t<xpath>%s/thingClass</xpath>\n\t\t<value><thingClass>CombatExtended.ProjectileCE_Explosive</thingClass></value>\n\t</Operation>' % (mr, sel))
    else:
        ops.append('\t<Operation Class="PatchOperationAdd"%s>\n\t\t<xpath>%s</xpath>\n\t\t<value><thingClass>CombatExtended.ProjectileCE_Explosive</thingClass></value>\n\t</Operation>' % (mr, sel))
    ops.append('\t<Operation Class="PatchOperationAdd"%s>\n\t\t<xpath>%s/projectile</xpath>\n\t\t<value>\n'
               '\t\t\t<explosionDamageFalloff>true</explosionDamageFalloff>\n\t\t\t<suppressionFactor>3.0</suppressionFactor>\n'
               '\t\t\t<dangerFactor>2.0</dangerFactor>\n\t\t\t<airborneSuppressionFactor>0.25</airborneSuppressionFactor>\n'
               '\t\t</value>\n\t</Operation>' % (mr, sel))
    if 'FragExplosion' in (d.findtext('thingClass') or ''):
        # FCP's own shrapnel class is replaced by CE's projectile, so hand the shrapnel to CE's fragment system
        count = int(num(d.find('modExtensions/li/projCount'), 12) * 3)
        frag = ('<li Class="CombatExtended.CompProperties_Fragments"><fragments><Fragment_Small>%d</Fragment_Small></fragments></li>' % count)
        ops.append('\t<Operation Class="PatchOperationConditional"%s>\n\t\t<xpath>%s/comps</xpath>\n'
                   '\t\t<match Class="PatchOperationAdd">\n\t\t\t<xpath>%s/comps</xpath>\n\t\t\t<value>%s</value>\n\t\t</match>\n'
                   '\t\t<nomatch Class="PatchOperationAdd">\n\t\t\t<xpath>%s</xpath>\n\t\t\t<value><comps>%s</comps></value>\n\t\t</nomatch>\n\t</Operation>'
                   % (mr, sel, sel, frag, sel, frag))
    return '\n'.join(ops)


def grenade_patch(d, report):
    dn = d.findtext('defName')
    v = verb_info(d)[0]
    proj = v.findtext('defaultProjectile')
    mass = num(inherited(d, 'statBases/Mass'), 0.5)
    label = v.findtext('label') or 'throw grenade'
    rng = num(v.find('range'), 12)
    warm = num(v.find('warmupTime'), 1.0)
    out = []
    for li in d.findall('verbs/li'):
        vclass = li.findtext('verbClass') or ''
        if vclass not in ('Verb_Shoot', 'Verb_ShootOneUse', 'Verb_LaunchProjectile'):
            out.append('\t<Operation Class="PatchOperationRemove"%s>\n\t\t<xpath>%s/verbs/li[verbClass="%s"]</xpath>\n\t</Operation>' % (may_require(d), selector(d), vclass))
    out.append('\t<Operation Class="CombatExtended.PatchOperationMakeGunCECompatible"%s>\n\t\t<defName>%s</defName>\n\t\t<statBases>\n'
               '\t\t\t<Bulk>%s</Bulk>\n\t\t\t<RangedWeapon_Cooldown>1</RangedWeapon_Cooldown>\n\t\t\t<SightsEfficiency>1.0</SightsEfficiency>\n\t\t</statBases>\n'
               '\t\t<Properties>\n\t\t\t<label>%s</label>\n\t\t\t<verbClass>CombatExtended.Verb_ShootCEOneUse</verbClass>\n'
               '\t\t\t<hasStandardCommand>true</hasStandardCommand>\n\t\t\t<range>%s</range>\n\t\t\t<minRange>4</minRange>\n'
               '\t\t\t<warmupTime>%s</warmupTime>\n\t\t\t<noiseRadius>4</noiseRadius>\n\t\t\t<ai_IsBuildingDestroyer>true</ai_IsBuildingDestroyer>\n'
               '\t\t\t<soundCast>ThrowGrenade</soundCast>\n\t\t\t<targetParams>\n\t\t\t\t<canTargetLocations>true</canTargetLocations>\n\t\t\t</targetParams>\n'
               '\t\t\t<defaultProjectile>%s</defaultProjectile>\n\t\t\t<onlyManualCast>true</onlyManualCast>\n\t\t\t<ignorePartialLoSBlocker>true</ignorePartialLoSBlocker>\n'
               '\t\t\t<ai_AvoidFriendlyFireRadius>7</ai_AvoidFriendlyFireRadius>\n\t\t\t<minRangeInCover>2</minRangeInCover>\n\t\t</Properties>\n'
               '\t\t<weaponTags>\n%s\t\t</weaponTags>\n\t</Operation>'
               % (may_require(d), dn, f2(max(0.3, round(mass * 1.7, 2))), escape(label), f2(rng * 0.8), f2(max(0.8, warm * 0.6)), proj,
                  ''.join('\t\t\t<li>%s</li>\n' % t for t in GRENADE_TAGS)))
    report.append('GRENADE %s' % dn)
    return '\n'.join(out)


# ---------------------------------------------------------------- driver
def wrap(ops):
    return '<?xml version="1.0" encoding="utf-8"?>\n<Patch>\n\n' + '\n\n'.join(ops) + '\n\n</Patch>\n'


def main():
    ammo_sets = load_ammo_sets()
    report = []
    pkgs = mod_packages()
    projectile_nodes_done = set()
    loadfolders = []
    stats = {}
    for mod, pkg in pkgs.items():
        defs = load_defs(mod)
        guns, grenades, tools, melee_bulk, apparel, races, projs = [], [], [], [], [], [], []
        for f, d in defs:
            dn = d.findtext('defName') or d.get('Name')
            if d.get('Class'):  # ignore non ThingDef-like specials
                pass
            abstract = d.get('Abstract') == 'True'
            verbs = verb_info(d)
            wt = inherited(d, 'weaponTags')
            is_weapon_like = bool(verbs) and not d.find('race') is not None
            if verbs and not abstract and (d.find('verbs') is not None or is_weapon_like) and d.find('apparel') is None and d.find('race') is None and d.find('projectile') is None:
                if is_grenade(d):
                    g = grenade_patch(d, report)
                    if g:
                        grenades.append(g)
                else:
                    g = gun_patch(d, ammo_sets, report)
                    if g:
                        guns.append(g)
            # projectile patches for grenade/explosive style projectiles (explosionRadius)
            pr = d.find('projectile')
            if pr is not None and pr.findtext('explosionRadius') and ('Grenade' in (d.get('ParentName') or '') or 'Grenade' in (dn or '') or (d.findtext('thingClass') or '').endswith('Explosive')):
                projs.append(grenade_projectile_patch(d))
            if d.find('tools') is not None and d.find('race') is None:
                t = tools_patch(d)
                if t:
                    tools.append(t)
                if d.find('apparel') is None and not abstract and not verbs:
                    melee_bulk.append(melee_bulk_patch(d))
            if d.find('race') is not None and d.find('tools') is not None:
                t = tools_patch(d)
                if t:
                    tools.append(t)
            if d.find('apparel') is not None:
                a = apparel_patch(d)
                if a:
                    apparel.append(a)
            if d.find('race') is not None:
                r = race_patch(d)
                if r:
                    races.append(r)
        # abstract grenade projectile bases (no explosionRadius on the base itself)
        for f, d in defs:
            if d.get('Name') == 'FCP_BaseGrenadeProjectile':
                projs.append(grenade_projectile_patch(d))

        files = {
            'Weapons_Guns.xml': guns,
            'Weapons_Grenades.xml': grenades + projs,
            'Melee_Tools.xml': tools + melee_bulk,
            'Apparel.xml': apparel,
            'Races.xml': races,
        }
        wrote = False
        for fname, ops in files.items():
            if not ops:
                continue
            p = os.path.join(OUT, 'Modules', mod, 'Patches')
            os.makedirs(p, exist_ok=True)
            with open(os.path.join(p, fname), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(wrap(ops))
            wrote = True
            stats[(mod, fname)] = len(ops)
        if wrote:
            loadfolders.append((pkg, 'Modules/' + mod))

    lf = ['<?xml version="1.0" encoding="utf-8"?>', '<loadFolders>', '\t<v1.6>']
    for pkg, folder in loadfolders:
        lf.append('\t\t<li IfModActive="%s">%s</li>' % (pkg, folder))
    lf += ['\t</v1.6>', '</loadFolders>', '']
    with open(os.path.join(OUT, 'LoadFolders.xml'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lf))

    with open(os.path.join(OUT, 'Tools', 'last_report.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(report) + '\n')
    for k in sorted(stats):
        print(k, stats[k])
    print('\n'.join(r for r in report if not r.startswith(('GUN', 'GRENADE'))))


if __name__ == '__main__':
    main()
