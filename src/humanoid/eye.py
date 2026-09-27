"""The robot's own eye: a first-person head view of the fetch room, and what it can actually see.

The largest honest gap in this programme is that every fact the decision layer reads comes from the simulator's ground
truth. Before asking whether a model could produce those facts from pixels, ask the cheaper and more fundamental question:
**is the fact even in the image?** A head camera has a field of view and the world occludes. If the person a safety clause
is about stands behind the robot, no perception system can report her distance, and that is a ceiling on the enterprise
rather than a defect of any particular model.

The camera is driven from the robot's pose rather than injected into the XML, because the G1's bodies live in an included
asset. Nothing about the bench changes unless this is used.
"""
import math, numpy as np, mujoco

FOVY = 58.0        # Intel RealSense D435i vertical field of view, the camera most G1 stacks actually carry
HEAD_Z = 1.25      # head height above the floor for a standing G1
NEAR_D = 0.35      # how far in front of the eye the look-at point sits

ROOM_POS = (1.0, 3.2, 2.9)      # a fixed camera high in a corner, the kind a warehouse or a home already has
DOOR_POS = (4.2, 2.4, 2.4)      # a fixed camera above the doorway, looking back into the room

class Eye:
    def __init__(self, model, width=320, height=240):
        self.model = model
        self.r = mujoco.Renderer(model, height=height, width=width)
        self.seg = mujoco.Renderer(model, height=height, width=width)
        self.seg.enable_segmentation_rendering()
        self.npix = width * height
        self.geom_body = {g: model.body(model.geom_bodyid[g]).name for g in range(model.ngeom)}
        self.cam = mujoco.MjvCamera(); self.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.cam.distance = NEAR_D; self.cam.elevation = 0.0
        for o in model.vis.global_.__dir__():
            pass
        model.vis.global_.fovy = FOVY

    def aim_at(self, eye_xyz, target_xyz):
        """Point a camera sitting at eye_xyz toward target_xyz. Used for fixed room cameras and the wrist view."""
        import numpy as _np
        e = _np.asarray(eye_xyz, float); t = _np.asarray(target_xyz, float)
        d = t - e; dist = float(_np.linalg.norm(d)) or 1e-6
        self.cam.lookat[:] = t
        self.cam.distance = dist
        self.cam.azimuth = math.degrees(math.atan2(d[1], d[0]))
        self.cam.elevation = math.degrees(math.asin(max(-1.0, min(1.0, d[2] / dist))))

    def aim(self, xy, yaw, z=HEAD_Z):
        """Point the eye out of the robot's head, along its heading."""
        f = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        self.cam.lookat[:] = np.array([xy[0], xy[1], z]) + f * NEAR_D
        self.cam.azimuth = math.degrees(yaw)
        self.cam.elevation = 0.0
        self.cam.distance = NEAR_D   # MUST be reset: aim_at() leaves it at the last fixed camera's range, which silently
        # turns this first-person view into a third-person one. Found by two runs of the same camera disagreeing 77 % to 26 %.

    def look(self, data):
        self.r.update_scene(data, camera=self.cam); rgb = self.r.render()
        self.seg.update_scene(data, camera=self.cam); s = self.seg.render()
        return rgb, s

    def visible(self, data, names):
        """Per body name: pixels occupied in the head view. Segmentation gives (objid, objtype) per pixel."""
        _, s = self.look(data)
        ids = s[:, :, 0]; types = s[:, :, 1]   # MuJoCo segmentation: channel 0 is the object id, channel 1 the object type
        gmask = types == mujoco.mjtObj.mjOBJ_GEOM
        out = {n: 0 for n in names}
        vis_ids, counts = np.unique(ids[gmask], return_counts=True)
        for gid, c in zip(vis_ids, counts):
            if 0 <= gid < self.model.ngeom:
                b = self.geom_body.get(int(gid))
                if b in out: out[b] += int(c)
        return {n: {"pixels": p, "visible": p > 0, "frac": p / self.npix} for n, p in out.items()}
