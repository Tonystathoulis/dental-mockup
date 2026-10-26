"""Dental3D Studio — desktop concept demo (illustrative, not clinically validated)."""
import sys
import math
import json
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QSlider,
    QComboBox, QFileDialog, QStatusBar, QButtonGroup, QSizePolicy)

BG = "#f5f7fb"
CARD = "#ffffff"
INK = "#192337"
MUTED = "#7d899d"
BLUE = "#6687f5"
LAV = "#a98aef"

STYLE = """
QWidget { font-family: 'Segoe UI'; color: #26354c; font-size: 13px; }
QMainWindow { background: #0d1729; }
QFrame#topbar, QFrame#sidebar, QFrame#rightpanel, QFrame#statuscard { background: #ffffff; border: 1px solid #dce5f1; border-radius: 14px; }
QFrame#viewportcard { background: #172742; border: 1px solid #2a3d5b; border-radius: 16px; }
QLabel#muted { color: #718099; }
QLabel#sectiontitle { font-size: 19px; font-weight: 700; color: #1d2b42; }
QLabel#brand { font-size: 19px; font-weight: 750; color: #23344f; }
QPushButton { background: #f3f7fc; border: 1px solid #dce5f1; border-radius: 9px; padding: 9px 12px; color: #34445f; font-weight: 600; }
QPushButton:hover { background: #eaf1fd; border-color: #b9cbed; }
QPushButton:checked { background: #dfeaff; color: #375ba6; border-color: #b9cbed; }
QPushButton:disabled { color: #687891; background: #f1f5fa; }
QPushButton#primary { background: #647ff0; color: white; border: 0; }
QPushButton#primary:hover { background: #7890ff; }
QPushButton#nav { text-align: left; padding: 12px; background: transparent; border-color: transparent; color: #62718a; }
QPushButton#nav:checked { background: #eaf1ff; color: #3e60ad; border-color: #d9e5fb; }
QComboBox { background: #ffffff; color: #1b2940; border: 1px solid #d4dce8; border-radius: 8px; padding: 9px; selection-background-color: #dce5ff; }
QComboBox QAbstractItemView { background: #ffffff; color: #1b2940; selection-background-color: #dce5ff; selection-color: #17233a; border: 1px solid #d4dce8; outline: 0; padding: 4px; }
QComboBox QAbstractItemView::item { min-height: 28px; padding: 4px 8px; }
QMenu { background: #ffffff; color: #1b2940; border: 1px solid #d4dce8; padding: 4px; }
QMenu::item { padding: 7px 24px; }
QMenu::item:selected { background: #dce5ff; color: #17233a; }
QSlider::groove:horizontal { background: #dfe6f0; height: 5px; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #7b91f2; border-radius: 2px; }
QSlider::handle:horizontal { background: white; border: 2px solid #7189f1; width: 13px; margin: -6px 0; border-radius: 7px; }
QStatusBar { color: #b7c4d9; }
"""

def label(text, name=None):
    w = QLabel(text)
    if name: w.setObjectName(name)
    return w

def card_layout(title=None):
    box = QFrame(); box.setStyleSheet("QFrame { background: #f5f8fd; border: 1px solid #e1e9f3; border-radius: 10px; }")
    lay = QVBoxLayout(box); lay.setContentsMargins(13, 12, 13, 12); lay.setSpacing(8)
    if title:
        t = label(title); t.setStyleSheet("font-weight: 700; color: #33435d; border: 0; background: transparent;")
        lay.addWidget(t)
    return box, lay

class DentalStudio(QMainWindow):
    SECTIONS = ["Scan Analysis", "Treatment Design", "Contact Analysis", "Scan Comparison"]
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dental3D Studio — Concept Demo")
        self.resize(1440, 900); self.setMinimumSize(1120, 720)
        self.current_section = 0; self.upper_visible = True; self.lower_visible = True
        self.treatment_visible = True; self.contact_visible = False; self.deviation_visible = False
        self.scan_b = False; self.imported = None; self.tooth_actors = {"upper": [], "lower": []}
        root = QWidget(); self.setCentralWidget(root)
        main = QVBoxLayout(root); main.setContentsMargins(18, 14, 18, 12); main.setSpacing(12)
        main.addWidget(self.make_topbar())
        body = QHBoxLayout(); body.setSpacing(12); main.addLayout(body, 1)
        body.addWidget(self.make_nav(), 0)
        self.viewport_card = QFrame(); self.viewport_card.setObjectName("viewportcard")
        vbox = QVBoxLayout(self.viewport_card); vbox.setContentsMargins(9, 9, 9, 9); vbox.setSpacing(7)
        self.plotter = QtInteractor(self.viewport_card); vbox.addWidget(self.plotter.interactor, 1)
        self.plotter.set_background("#172742", top="#213451")
        self.plotter.enable_anti_aliasing("ssaa")
        self.build_model(); self.plotter.view_isometric(); self.plotter.camera.zoom(1.25)
        self.viewport_hint = QLabel("DRAG TO ROTATE  ·  SCROLL TO ZOOM  ·  SHIFT + DRAG TO PAN")
        self.viewport_hint.setAlignment(Qt.AlignCenter); self.viewport_hint.setStyleSheet("color:#c0cce0; font-size:10px; letter-spacing:1px; background:transparent; padding:3px;")
        vbox.addWidget(self.viewport_hint)
        body.addWidget(self.viewport_card, 1)
        body.addWidget(self.make_right(), 0)
        self.make_status(main)
        self.refresh_panel()

    def make_topbar(self):
        bar = QFrame(); bar.setObjectName("topbar"); bar.setFixedHeight(66)
        lay = QHBoxLayout(bar); lay.setContentsMargins(18, 8, 14, 8); lay.setSpacing(12)
        brand = label("◈  Dental3D Studio", "brand"); lay.addWidget(brand)
        lay.addWidget(label("CONCEPT DEMO", "muted")); lay.addStretch()
        case = QPushButton("▣  Demo Case 001"); case.setEnabled(False); lay.addWidget(case)
        op = QPushButton("↥  Open Scan"); op.clicked.connect(self.open_scan); lay.addWidget(op)
        save = QPushButton("▣  Save Session"); save.clicked.connect(self.save_session); lay.addWidget(save)
        reset = QPushButton("⟳  Reset View"); reset.clicked.connect(self.reset_view); lay.addWidget(reset)
        return bar

    def make_nav(self):
        panel = QFrame(); panel.setObjectName("sidebar"); panel.setFixedWidth(206)
        lay = QVBoxLayout(panel); lay.setContentsMargins(12, 16, 12, 12); lay.setSpacing(7)
        lay.addWidget(label("WORKSPACE", "muted"))
        self.nav_group = QButtonGroup(self); self.nav_group.setExclusive(True)
        for i, (icon, title) in enumerate(zip(["◉", "✧", "◌", "⇄"], self.SECTIONS)):
            b = QPushButton(f"{icon}   {title}"); b.setObjectName("nav"); b.setCheckable(True); b.setChecked(i == 0)
            self.nav_group.addButton(b, i); lay.addWidget(b)
        self.nav_group.idClicked.connect(self.change_section)
        lay.addStretch()
        jaw, jl = card_layout("VISIBLE JAWS")
        self.upper_btn = QPushButton("●  Upper jaw"); self.upper_btn.setCheckable(True); self.upper_btn.setChecked(True); self.upper_btn.clicked.connect(self.toggle_upper)
        self.lower_btn = QPushButton("●  Lower jaw"); self.lower_btn.setCheckable(True); self.lower_btn.setChecked(True); self.lower_btn.clicked.connect(self.toggle_lower)
        jl.addWidget(self.upper_btn); jl.addWidget(self.lower_btn); lay.addWidget(jaw)
        return panel

    def make_right(self):
        panel = QFrame(); panel.setObjectName("rightpanel"); panel.setFixedWidth(292)
        self.right_layout = QVBoxLayout(panel); self.right_layout.setContentsMargins(16, 17, 16, 14); self.right_layout.setSpacing(10)
        self.right_panel = panel
        return panel

    def make_status(self, main):
        status = QFrame(); status.setObjectName("statuscard"); status.setFixedHeight(38)
        lay = QHBoxLayout(status); lay.setContentsMargins(14, 3, 14, 3)
        self.status_msg = label("●  Demo model loaded  ·  All measurements are illustrative", "muted")
        lay.addWidget(self.status_msg); lay.addStretch()
        badge = label("●  DEMO MODE"); badge.setStyleSheet("color:#3e60ad; background:#eaf1ff; border-radius:9px; padding:5px 10px; font-weight:700; font-size:11px;")
        lay.addWidget(badge); main.addWidget(status)
        sb = QStatusBar(); sb.setSizeGripEnabled(False); sb.setStyleSheet("QStatusBar{background:transparent;border:0;color:#7d899d;}")
        self.setStatusBar(sb)

    def add_tooth(self, jaw, idx, x, y, z, slope):
        # Incisors sit at the center of the arch; canines and broad molars curve toward the back.
        frontness = abs(idx - 6.5)
        if frontness < 0.6: width, depth = 0.155, 0.20
        elif frontness < 1.6: width, depth = 0.16, 0.21
        elif frontness < 2.6: width, depth = 0.175, 0.23
        elif frontness < 4.4: width, depth = 0.19, 0.245
        else: width, depth = 0.21, 0.26
        crown_center = z + (0.08 if jaw == "upper" else -0.08)
        s = pv.Sphere(theta_resolution=36, phi_resolution=28, radius=1.0)
        pts = s.points.copy()
        # Slightly flattened gumline, broad occlusal surface and a subtle pinched cervical waist.
        zshape = np.sign(pts[:, 2]) * np.abs(pts[:, 2]) ** 0.78
        pts[:, 0] *= width; pts[:, 1] *= depth; pts[:, 2] = zshape * 0.29
        if frontness >= 2.6:
            # Four shallow cusps give premolars and molars a recognizable chewing surface.
            xx, yy = pts[:, 0] / width, pts[:, 1] / depth
            cusp_relief = np.zeros(len(pts))
            for cx, cy in [(-0.42, -0.35), (0.42, -0.35), (-0.42, 0.35), (0.42, 0.35)]:
                cusp_relief += 0.025 * np.exp(-((xx-cx)**2 + (yy-cy)**2) / 0.045)
            pts[:, 2] += cusp_relief * np.maximum(pts[:, 2] / 0.29, 0) ** 2
        # Round the cervical edge and slightly flatten the incisal/chewing surface for tooth-like crowns.
        radial = np.sqrt(pts[:, 0] ** 2 + pts[:, 1] ** 2)
        pts[:, 2] *= 0.96 + 0.04 * np.cos(radial * math.pi)
        crown = pv.PolyData(pts, s.faces)
        crown.translate((x, y, crown_center), inplace=True)
        crown.rotate_z(math.degrees(math.atan(slope)), point=(x, y, crown_center), inplace=True)
        color = "#fffaf0" if jaw == "upper" else "#f4f0ff"
        actor = self.plotter.add_mesh(crown, color=color, smooth_shading=True, specular=0.48, specular_power=28,
            ambient=0.24, diffuse=0.8, show_edges=False)
        self.tooth_actors[jaw].append(actor)

    def build_model(self):
        self.plotter.clear()
        self.tooth_actors = {"upper": [], "lower": []}
        # 14 teeth per arch along a gentle horseshoe curve; incisors at the front (negative Y).
        for jaw, z in [("upper", 0.55), ("lower", -0.55)]:
            for i in range(14):
                u = (i - 6.5) / 6.5
                x = u * 2.28
                y = -1.5 + 1.38 * (abs(u) ** 1.65)
                y += 0.06 * math.cos(i * 0.65)
                slope = 1.38 * 1.65 * (abs(u) ** 0.65) * (1 if u >= 0 else -1) / 2.28
                self.add_tooth(jaw, i, x, y, z, slope)
        # Soft gingival horseshoes behind each row.
        for z, color in [(0.48, "#c47c86"), (-0.48, "#b986b8")]:
            t = np.linspace(-2.28, 2.28, 100)
            u = t / 2.28
            yy = -1.5 + 1.38 * np.abs(u) ** 1.65 + 0.25
            gum = pv.Spline(np.c_[t, yy, np.full_like(t, z)], 150).tube(radius=0.14, n_sides=24)
            self.tooth_actors["upper" if z > 0 else "lower"].append(
                self.plotter.add_mesh(gum, color=color, smooth_shading=True, opacity=0.95, specular=0.2))
        self.plotter.add_axes(line_width=1)
        self.plotter.reset_camera()
        if hasattr(self, "imported") and self.imported is not None:
            self.import_actor = self.plotter.add_mesh(self.imported, color="#c5d8ee", opacity=0.75, smooth_shading=True)
        self.update_visibility()
        self.update_overlays()

    def update_visibility(self):
        for actor in self.tooth_actors["upper"]: actor.SetVisibility(self.upper_visible)
        for actor in self.tooth_actors["lower"]: actor.SetVisibility(self.lower_visible)
        self.plotter.render()

    def toggle_upper(self, checked): self.upper_visible = checked; self.update_visibility()
    def toggle_lower(self, checked): self.lower_visible = checked; self.update_visibility()
    def reset_view(self):
        self.plotter.view_isometric(); self.plotter.reset_camera(); self.plotter.camera.zoom(1.22); self.plotter.render()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0); w = item.widget()
            if w:
                w.hide()
                w.deleteLater()

    def heading(self, title, subtitle):
        self.right_layout.addWidget(label(title, "sectiontitle")); self.right_layout.addWidget(label(subtitle, "muted"))

    def metric_card(self, title, rows):
        box, lay = card_layout(title)
        for name, value in rows:
            row = QHBoxLayout(); row.addWidget(label(name, "muted")); row.addStretch()
            val = label(value); val.setStyleSheet("font-weight:700; color:#26354c; background:transparent; border:0;")
            row.addWidget(val); lay.addLayout(row)
        self.right_layout.addWidget(box)

    def refresh_panel(self):
        self.clear_layout(self.right_layout)
        if self.current_section == 0:
            self.heading("Scan Analysis", "Overview of the current demo scan")
            self.metric_card("MODEL SUMMARY", [("Total teeth", "28"), ("Upper arch", "14 teeth"), ("Lower arch", "14 teeth"), ("Scan quality", "Good · 96%")])
            self.metric_card("ILLUSTRATIVE MEASUREMENTS", [("Arch width", "52.4 mm"), ("Overjet", "2.1 mm"), ("Midline offset", "0.4 mm")])
            self.info_note("Demo values", "Measurements shown here are sample values for presentation only.")
        elif self.current_section == 1:
            self.heading("Treatment Design", "Preview a restorative concept")
            self.right_layout.addWidget(label("DESIGN TYPE", "muted"))
            combo = QComboBox(); combo.addItems(["Retainer", "Crown / Restoration", "Implant-Related Restoration"]); self.right_layout.addWidget(combo)
            show = QPushButton("◉   Show Treatment"); show.setCheckable(True); show.setChecked(self.treatment_visible); show.clicked.connect(self.toggle_treatment); self.right_layout.addWidget(show)
            self.right_layout.addWidget(label("TREATMENT OPACITY", "muted"))
            slider = QSlider(Qt.Horizontal); slider.setRange(15, 100); slider.setValue(78); slider.valueChanged.connect(self.set_treatment_opacity); self.right_layout.addWidget(slider)
            alt = QPushButton("✧   Alternative Design"); alt.setObjectName("primary"); alt.clicked.connect(self.alternative_design); self.right_layout.addWidget(alt)
            self.metric_card("DESIGN PREVIEW", [("Material", "Ceramic · sample"), ("Fit score", "92% · illustrative"), ("Status", "Concept ready")])
            self.info_note("Concept only", "Treatment geometry is an illustrative overlay, not a clinical design.")
        elif self.current_section == 2:
            self.heading("Contact Analysis", "Visualize occlusal proximity")
            toggle = QPushButton("◉   Contact Map Overlay"); toggle.setCheckable(True); toggle.setChecked(self.contact_visible); toggle.clicked.connect(self.toggle_contact); self.right_layout.addWidget(toggle)
            box, lay = card_layout("CONTACT LEGEND")
            for c, t in [("#ff6689", "High contact"), ("#ffb65d", "Light contact"), ("#65c7b0", "Clearance")]:
                row = QHBoxLayout(); sw = QLabel("  "); sw.setStyleSheet(f"background:{c}; border-radius:4px; min-width:14px; max-width:14px; min-height:14px; max-height:14px; border:0;")
                row.addWidget(sw); row.addWidget(label(t, "muted")); lay.addLayout(row)
            self.right_layout.addWidget(box)
            self.metric_card("SIMULATED EXAMPLE", [("Closest clearance", "0.18 mm"), ("Contact regions", "6 areas"), ("Peak intensity", "Moderate")])
            self.info_note("Simulated analysis", "Colored regions and clearance values are example data; no contact calculation is performed.")
        else:
            self.heading("Scan Comparison", "Compare two illustrative scan states")
            self.right_layout.addWidget(label("ACTIVE SCAN", "muted"))
            combo = QComboBox(); combo.addItems(["Scan A  ·  Baseline", "Scan B  ·  Follow-up"]); combo.setCurrentIndex(int(self.scan_b)); combo.currentIndexChanged.connect(self.switch_scan); self.right_layout.addWidget(combo)
            overlay = QPushButton("⇄   Show Overlay"); overlay.setCheckable(True); overlay.setChecked(self.deviation_visible); overlay.clicked.connect(self.toggle_deviation); self.right_layout.addWidget(overlay)
            self.metric_card("COMPARISON SUMMARY", [("Reference", "Scan A"), ("Current", "Scan B"), ("Mean deviation", "+0.12 mm"), ("Max deviation", "+0.38 mm")])
            self.info_note("Illustrative comparison", "Scan states and deviation values are simulated for the demo.")
        self.right_layout.addStretch()
        self.update_overlays()

    def info_note(self, title, body):
        box, lay = card_layout(title); msg = label(body); msg.setWordWrap(True); msg.setStyleSheet("color:#64748a; font-size:12px; border:0; background:transparent;")
        lay.addWidget(msg); self.right_layout.addWidget(box)

    def remove_overlay(self, attr):
        actors = getattr(self, attr, [])
        for a in actors:
            try: self.plotter.remove_actor(a)
            except Exception: pass
        setattr(self, attr, [])

    def update_overlays(self):
        self.remove_overlay("contact_actors"); self.remove_overlay("treatment_actors"); self.remove_overlay("deviation_actors")
        if self.current_section == 1 and self.treatment_visible:
            alt = getattr(self, "alternative", False)
            m = pv.Sphere(radius=0.15 if alt else 0.17, center=(0.12 if alt else 0.0, -1.5, 0.66), theta_resolution=32, phi_resolution=24)
            self.treatment_actors = [self.plotter.add_mesh(m, color="#8ca1ff", opacity=getattr(self, "treatment_opacity", .78), smooth_shading=True, specular=.5)]
        if self.current_section == 2 and self.contact_visible:
            self.contact_actors = []
            for x, y, c in [(-.7,-1.48,"#ff6689"),(.05,-1.52,"#ffb65d"),(.78,-1.44,"#ff6689"),(-1.4,-1.25,"#65c7b0"),(1.4,-1.23,"#ffb65d")]:
                m = pv.Sphere(radius=.10, center=(x,y,.91), theta_resolution=18, phi_resolution=14)
                self.contact_actors.append(self.plotter.add_mesh(m, color=c, opacity=.9, smooth_shading=True))
        if self.current_section == 3 and self.deviation_visible:
            m = pv.Sphere(radius=.14, center=(.4,-1.4,.91), theta_resolution=22, phi_resolution=16)
            self.deviation_actors = [self.plotter.add_mesh(m, color="#b087f2", opacity=.88, smooth_shading=True)]
        self.plotter.render()

    def change_section(self, index): self.current_section = index; self.refresh_panel()
    def toggle_treatment(self, on): self.treatment_visible = on; self.update_overlays()
    def set_treatment_opacity(self, value):
        self.treatment_opacity = value / 100
        self.update_overlays()
    def alternative_design(self):
        self.alternative = not getattr(self, "alternative", False)
        self.statusBar().showMessage("Alternative contour selected" if self.alternative else "Standard contour restored", 3000)
        self.update_overlays()
    def toggle_contact(self, on): self.contact_visible = on; self.update_overlays()
    def toggle_deviation(self, on): self.deviation_visible = on; self.update_overlays()
    def switch_scan(self, index):
        self.scan_b = bool(index)
        # Small positional shift makes the two illustrative states visibly distinct.
        for actors in self.tooth_actors.values():
            for actor in actors:
                actor.SetPosition((0.035 if self.scan_b else 0, 0, 0))
        self.update_overlays()

    def open_scan(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open dental scan", "", "STL Mesh (*.stl);;PLY Mesh (*.ply);;All files (*)")
        if not path: return
        try:
            mesh = pv.read(path)
            if not isinstance(mesh, pv.PolyData) or mesh.n_points == 0: raise ValueError("The selected file does not contain a surface mesh.")
            self.imported = mesh; self.build_model(); self.reset_view()
            self.status_msg.setText(f"●  Imported scan: {path.split('/')[-1]}")
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Could not open scan", f"This scan could not be loaded.\n\n{exc}")

    def save_session(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save demo session", "Dental3D-Demo-Session.json", "Session file (*.json)")
        if not path: return
        data = {
            "case": "Demo Case 001", "section": self.SECTIONS[self.current_section],
            "upper_jaw_visible": self.upper_visible, "lower_jaw_visible": self.lower_visible,
            "scan": "B" if self.scan_b else "A", "treatment_visible": self.treatment_visible,
            "contact_map_visible": self.contact_visible, "deviation_map_visible": self.deviation_visible,
            "notice": "Concept demo state; no clinical data or calculations."
        }
        try:
            with open(path, "w", encoding="utf-8") as stream: json.dump(data, stream, indent=2)
            self.statusBar().showMessage("Demo session saved", 4000)
        except OSError as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Could not save session", f"The session file could not be saved.\n\n{exc}")

    def closeEvent(self, event):
        self.plotter.close(); super().closeEvent(event)

def main():
    app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(STYLE)
    win = DentalStudio(); win.show(); sys.exit(app.exec())

if __name__ == "__main__": main()
