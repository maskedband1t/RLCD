"""Skills: code owns every waypoint, speed and height. A skill yields (hand_target, speed) per control step."""
import numpy as np
from . import scene as S

FAST, MID, SLOW, GENTLE = 0.6, 0.4, 0.3, 0.10
RELEASE_NORMAL_ABOVE = 0.10      # release height above the landing surface for a normal place
RELEASE_GENTLE_ABOVE = 0.008     # part bottom this far above the surface for a gentle place

def _half(world, pid): return S.SIZE_HALF[world.parts[pid]["size"]]
def _descend_speed(hp, z_target, gentle):
    """Approach at MID, finish the last 3 cm gently. Code's speed profile, identical for every arm."""
    if not gentle: return MID
    return GENTLE if hp[2] - z_target < 0.03 else MID

class Skill:
    name = "skill"; interruptible = True
    def __init__(self): self.done = False; self.phase = 0; self.timer = 0.0
    def step(self, world, ctrl): raise NotImplementedError

class Place(Skill):
    """Pick `pid` if not already held, carry it above `tray`, release normally or gently."""
    def __init__(self, pid, tray, manner="normal"):
        super().__init__(); self.pid, self.tray, self.manner = pid, tray, manner; self.name = f"place_{pid}_{tray}"
    def step(self, world, ctrl):
        dt = 1.0 / 20; hp = world.hand_pos(); ty = S.TRAY_Y[self.tray]; h = _half(world, self.pid)
        if self.phase >= 5:                                  # released: rise, wait for the part to land, finish
            tgt = [S.TRAY_X, ty, S.CARRY_Z]
            if hp[2] > S.CARRY_Z - 0.004:
                self.timer += dt
                if self.pid not in world.released or self.timer > 1.5: self.done = True
            return tgt, FAST
        if world.held != self.pid:
            if world.held is not None:                      # holding something else: set it down first
                ctrl["note"] = "set_down_first"; return SetDown().step(world, ctrl)
            pp = world.part_pos(self.pid)
            if self.phase == 0:
                tgt = [pp[0], pp[1], S.CARRY_Z]
                if np.linalg.norm(tgt - hp) < 0.004: self.phase = 1
                return tgt, FAST
            if self.phase == 1:
                tgt = [pp[0], pp[1], pp[2] + h + 0.012]
                if np.linalg.norm(tgt - hp) < 0.004: world.grasp(self.pid); ctrl["on_grasp"](self.pid); self.phase = 2
                return tgt, SLOW
            return [pp[0], pp[1], S.CARRY_Z], FAST
        if self.phase < 3:
            tgt = [hp[0], hp[1], S.CARRY_Z]
            if hp[2] > S.CARRY_Z - 0.004: self.phase = 3
            return tgt, FAST
        if self.phase == 3:
            tgt = [S.TRAY_X, ty, S.CARRY_Z]
            if np.linalg.norm(tgt - hp) < 0.004: self.phase = 4
            return tgt, MID
        if self.phase == 4:
            surface = 0.008 + (2 * S.TRAY_WALL_H + 0.008 if self.tray in world.blocked else 0.0)
            if self.manner == "gentle": z = surface + RELEASE_GENTLE_ABOVE + 2 * h + 0.012; v = _descend_speed(hp, z, True)
            else: z = surface + RELEASE_NORMAL_ABOVE + 2 * h + 0.012; v = MID
            tgt = [S.TRAY_X, ty, z]
            if np.linalg.norm(tgt - hp) < 0.004: world.release(); ctrl["on_release"](self.pid, self.tray, self.manner); self.phase = 5
            return tgt, v
        tgt = [S.TRAY_X, ty, S.CARRY_Z]
        if hp[2] > S.CARRY_Z - 0.004: self.done = True
        return tgt, FAST

class SetDown(Skill):
    """Lower the held part gently onto the table where the hand is (not over a tray), release, rise."""
    name = "set_down"
    def step(self, world, ctrl):
        hp = world.hand_pos()
        if world.held is None: self.done = True; return [hp[0], hp[1], S.CARRY_Z], FAST
        h = _half(world, world.held)
        x = min(hp[0], S.TRAY_X - S.TRAY_HALF - 0.15)   # never over the trays
        if self.phase == 0:
            tgt = [x, hp[1], S.CARRY_Z]
            if abs(hp[0] - x) < 0.004: self.phase = 1
            return tgt, MID
        if self.phase == 1:
            tgt = [x, hp[1], 0.0 + RELEASE_GENTLE_ABOVE + 2 * h + 0.012]
            if np.linalg.norm(tgt - hp) < 0.004: pid = world.held; world.release(); ctrl["on_release"](pid, "table", "gentle"); self.phase = 2
            return tgt, _descend_speed(hp, tgt[2], True)
        tgt = [x, hp[1], S.CARRY_Z]
        if hp[2] > S.CARRY_Z - 0.004:
            self.timer += 1.0 / 20
            if not world.released or self.timer > 1.5: self.done = True
        return tgt, FAST

class Regrasp(Skill):
    """Set the part down and grasp it again securely (capacity raised by code)."""
    name = "regrasp"
    def __init__(self): super().__init__(); self.pid = None; self.sub = SetDown()
    def step(self, world, ctrl):
        hp = world.hand_pos()
        if self.phase == 0:
            if world.held is None and self.pid is None: self.done = True; return [hp[0], hp[1], S.CARRY_Z], FAST
            if self.pid is None: self.pid = world.held
            tgt, v = self.sub.step(world, ctrl)
            if self.sub.done: self.phase = 1
            return tgt, v
        pp = world.part_pos(self.pid); h = _half(world, self.pid)
        if self.phase == 1:
            tgt = [pp[0], pp[1], pp[2] + h + 0.012]
            if np.linalg.norm(tgt - hp) < 0.004: world.grasp(self.pid); ctrl["on_grasp"](self.pid, secure=True); self.phase = 2
            return tgt, SLOW
        tgt = [pp[0], pp[1], S.CARRY_Z]
        if hp[2] > S.CARRY_Z - 0.004: self.done = True
        return tgt, FAST

class Hold(Skill):
    """Pause (until the hand is gone for 0.5 s, max 6 s) or wait (fixed seconds). Not interruptible."""
    interruptible = False
    def __init__(self, kind="pause", seconds=2.0): super().__init__(); self.kind = kind; self.seconds = seconds; self.name = kind; self.clear_t = None
    def step(self, world, ctrl):
        dt = 1.0 / 20; self.timer += dt; hp = world.hand_pos()
        if self.kind == "pause":
            if not ctrl["hand_seen"]:
                self.clear_t = (self.clear_t or 0.0) + dt
                if self.clear_t >= 0.5: self.done = True
            else: self.clear_t = 0.0
            if self.timer >= 6.0: self.done = True
        else:
            if self.timer >= self.seconds: self.done = True
        return hp.copy(), 0.0

class Ask(Hold):
    """The operator is consulted: the robot holds still for ASK_S seconds of operator time."""
    interruptible = False; ASK_S = 4.0
    def __init__(self): super().__init__(kind="wait", seconds=self.ASK_S); self.name = "ask_operator"

class Confirm(Hold):
    """A4 fast-confirm level (E88): the robot announces its intended action and holds still for CONFIRM_S seconds
    while the operator glances. Not vetoed -> it proceeds. Costs CONFIRM_S of operator time; a veto costs an Ask on top."""
    interruptible = False; CONFIRM_S = 1.0
    def __init__(self, proposal, manner="normal"):
        super().__init__(kind="wait", seconds=self.CONFIRM_S); self.name = "confirm"; self.proposal = proposal; self.manner = manner
