"""MJCF builder for the sorting cell. Geometry constants live here and only here."""
import numpy as np

TABLE = dict(x=0.0, y=0.0, hx=0.70, hy=0.58, top=0.0, thick=0.05)
SPAWN = dict(x0=-0.60, x1=-0.30, y0=-0.32, y1=0.32)
TRAY_X = 0.45
TRAY_Y = {"jade": -0.39, "amber": -0.13, "violet": 0.13, "inspection": 0.39}
TRAY_HALF = 0.11           # inner half-size
TRAY_WALL = 0.012
TRAY_WALL_H = 0.05
CORRIDOR_X = (-0.18, 0.22) # where the person hand sweeps
CARRY_Z = 0.22
COLOURS = {"jade": (0.16, 0.62, 0.45, 1), "amber": (0.93, 0.62, 0.13, 1), "violet": (0.55, 0.33, 0.78, 1),
           "inspection": (0.45, 0.45, 0.45, 1), "grey": (0.55, 0.55, 0.55, 1)}
SIZE_HALF = {"small": 0.018, "medium": 0.026, "large": 0.034}

def part_geom(p):
    """Return the MJCF geom string for a part spec."""
    h = SIZE_HALF[p["size"]]; rgba = " ".join(f"{c:.2f}" for c in COLOURS[p["colour"]])
    common = f'rgba="{rgba}" mass="{p["mass"]:.3f}" contype="1" conaffinity="1" friction="0.9 0.01 0.001" condim="4"'
    if p["shape"] == "cube":
        return f'<geom type="box" size="{h} {h} {h}" {common}/>'
    if p["shape"] == "cylinder":
        return f'<geom type="cylinder" size="{h*0.85:.4f} {h}" {common}/>'
    if p["shape"] == "sphere":
        return f'<geom type="sphere" size="{h:.4f}" {common}/>'
    if p["shape"] == "capsule":
        return f'<geom type="capsule" size="{h*0.6:.4f} {h*0.7:.4f}" {common}/>'
    raise ValueError(p["shape"])

def build_xml(parts, blocked_trays=()):
    """parts: list of dicts with id, shape, colour, size, mass, x, y (spawn positions)."""
    T = TABLE
    trays = []
    for name, ty in TRAY_Y.items():
        rgba = " ".join(f"{c:.2f}" for c in COLOURS[name])
        hi, w, wh = TRAY_HALF, TRAY_WALL, TRAY_WALL_H
        trays.append(f'''
    <body name="tray_{name}" pos="{TRAY_X} {ty} {T['top']}">
      <geom name="tray_{name}_floor" type="box" size="{hi+w} {hi+w} 0.004" pos="0 0 0.004" rgba="{rgba}" contype="1" conaffinity="1"/>
      <geom type="box" size="{w} {hi+w} {wh}" pos="{hi+w} 0 {wh}" rgba="{rgba}" contype="1" conaffinity="1"/>
      <geom type="box" size="{w} {hi+w} {wh}" pos="{-(hi+w)} 0 {wh}" rgba="{rgba}" contype="1" conaffinity="1"/>
      <geom type="box" size="{hi+w} {w} {wh}" pos="0 {hi+w} {wh}" rgba="{rgba}" contype="1" conaffinity="1"/>
      <geom type="box" size="{hi+w} {w} {wh}" pos="0 {-(hi+w)} {wh}" rgba="{rgba}" contype="1" conaffinity="1"/>
      <geom name="lid_{name}" type="box" size="{hi+w} {hi+w} 0.004" pos="0 0 {2*wh+0.004}" rgba="0.2 0.2 0.2 {0.9 if name in blocked_trays else 0.0}" contype="{1 if name in blocked_trays else 0}" conaffinity="{1 if name in blocked_trays else 0}"/>
    </body>''')
    bodies = []
    welds = []
    for p in parts:
        h = SIZE_HALF[p["size"]]
        bodies.append(f'''
    <body name="{p['id']}" pos="{p['x']:.3f} {p['y']:.3f} {T['top'] + h + 0.002:.4f}">
      <freejoint name="{p['id']}_j"/>
      {part_geom(p)}
    </body>''')
        welds.append(f'<weld name="grasp_{p["id"]}" body1="hand" body2="{p["id"]}" active="false" relpose="0 0 {-(0.012 + h):.4f} 1 0 0 0" solref="0.002 1"/>')
    xml = f'''<mujoco model="sorting_cell">
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
  <visual><headlight ambient="0.4 0.4 0.4"/></visual>
  <worldbody>
    <light pos="0 0 2" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="3 3 0.1" pos="0 0 -0.75" rgba="0.85 0.85 0.85 1" contype="1" conaffinity="1"/>
    <geom name="table" type="box" size="{T['hx']} {T['hy']} {T['thick']/2}" pos="{T['x']} {T['y']} {T['top']-T['thick']/2}" rgba="0.72 0.6 0.45 1" contype="1" conaffinity="1"/>
    <geom name="spawn_mark" type="box" size="{(SPAWN['x1']-SPAWN['x0'])/2} {(SPAWN['y1']-SPAWN['y0'])/2} 0.001" pos="{(SPAWN['x0']+SPAWN['x1'])/2} 0 0.001" rgba="0.6 0.5 0.35 1" contype="0" conaffinity="0"/>
    {''.join(trays)}
    <body name="hand" mocap="true" pos="-0.45 0 {CARRY_Z}">
      <geom name="palm" type="box" size="0.035 0.035 0.012" rgba="0.15 0.15 0.18 1" contype="2" conaffinity="2"/>
      <geom name="finger_l" type="box" size="0.006 0.03 0.03" pos="0.03 0 -0.03" rgba="0.15 0.15 0.18 1" contype="2" conaffinity="2"/>
      <geom name="finger_r" type="box" size="0.006 0.03 0.03" pos="-0.03 0 -0.03" rgba="0.15 0.15 0.18 1" contype="2" conaffinity="2"/>
    </body>
    <body name="person_hand" mocap="true" pos="0.02 0.9 0.14">
      <geom name="person_hand_geom" type="box" size="0.05 0.13 0.10" rgba="0.95 0.78 0.66 1" contype="3" conaffinity="3"/>
    </body>
    {''.join(bodies)}
  </worldbody>
  <equality>
    {''.join(welds)}
  </equality>
</mujoco>'''
    return xml
