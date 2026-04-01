import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import pint

# Initialize pint registry
u = pint.get_application_registry()

st.set_page_config(page_title="Coil Estimates", layout="wide")
st.title("Electromagnet Coil & Projectile Estimator")

# --- HELPER FUNCTION ---
def awg_diameter(n):
    """Calculate bare wire diameter (mm) from AWG number."""
    return 0.127 * 92 ** ((36 - n) / 39)

# --- SIDEBAR INPUTS ---
st.sidebar.header("Input Parameters")

conductor_type = st.sidebar.radio("Conductor Type", ["Round Wire (AWG)", "Round Wire (mm²)", "Foil / Strip Copper"])

if conductor_type == "Round Wire (AWG)":
    awg = st.sidebar.number_input("Wire AWG", min_value=1, max_value=40, value=20, step=1)
    
    t_enamel_thou = st.sidebar.number_input("Enamel Thickness (thou)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
    t_enamel_mm = t_enamel_thou * 0.0254
    st.sidebar.caption(f"*(Metric equivalent: {t_enamel_mm:.4f} mm)*")
    
    d_cu_val = awg_diameter(awg)
    d_total_val = d_cu_val + (2 * t_enamel_mm)
    
    A_cu_val = np.pi * (d_cu_val / 2) ** 2             
    A_total_val = np.pi * (d_total_val / 2) ** 2   

    # Orthocyclic limit = pi / (2 * sqrt(3)) ≈ 0.9069
    geom_limit = np.pi / (2 * np.sqrt(3))
    # Copper Space Factor scales the geometric limit by the bare-to-total area ratio
    f_cu_default = geom_limit * (A_cu_val / A_total_val)
    
    L_val = st.sidebar.number_input("Solenoid Length 'L' (mm)", value=20.0)
    
    # UI Labels for Round Wire
    lbl_cu_dim = "Bare Cu Diameter"
    val_cu_dim = d_cu_val
    cap_cu_dim = f"0.127 × 92^((36-{awg})/39)"
    
    lbl_tot_dim = "Total Wire Dia. (with enamel)"
    val_tot_dim = d_total_val
    cap_tot_dim = f"{d_cu_val:.3f} mm + 2({t_enamel_mm:.4f} mm)"
    
    cap_area_cu = f"π × ({d_cu_val:.3f} mm / 2)²"
    cap_area_tot = f"π × ({d_total_val:.3f} mm / 2)²"
    
    csv_conductor = f"AWG {awg}"
    csv_insulation = f"{t_enamel_thou} thou Enamel"

elif conductor_type == "Round Wire (mm²)":
    A_cu_input = st.sidebar.number_input("Bare Cu Area (mm²)", min_value=0.001, value=0.520, step=0.01, format="%.3f")
    
    t_enamel_thou = st.sidebar.number_input("Enamel Thickness (thou)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
    t_enamel_mm = t_enamel_thou * 0.0254
    st.sidebar.caption(f"*(Metric equivalent: {t_enamel_mm:.4f} mm)*")
    
    # Reverse calculate diameter from area
    d_cu_val = 2 * np.sqrt(A_cu_input / np.pi)
    d_total_val = d_cu_val + (2 * t_enamel_mm)
    
    A_cu_val = A_cu_input
    A_total_val = np.pi * (d_total_val / 2) ** 2   

    # Orthocyclic limit = pi / (2 * sqrt(3)) ≈ 0.9069
    geom_limit = np.pi / (2 * np.sqrt(3))
    f_cu_default = geom_limit * (A_cu_val / A_total_val)
    
    L_val = st.sidebar.number_input("Solenoid Length 'L' (mm)", value=20.0)
    
    # UI Labels for Round Wire (mm²)
    lbl_cu_dim = "Bare Cu Diameter"
    val_cu_dim = d_cu_val
    cap_cu_dim = f"Derived from {A_cu_val:.3f} mm²"
    
    lbl_tot_dim = "Total Wire Dia. (with enamel)"
    val_tot_dim = d_total_val
    cap_tot_dim = f"{d_cu_val:.3f} mm + 2({t_enamel_mm:.4f} mm)"
    
    cap_area_cu = "User Input"
    cap_area_tot = f"π × ({d_total_val:.3f} mm / 2)²"
    
    csv_conductor = f"{A_cu_val:.3f} mm² Wire"
    csv_insulation = f"{t_enamel_thou} thou Enamel"

else:
    foil_width = st.sidebar.selectbox("Foil Width (mm)", [11.0, 16.5])
    L_val = foil_width
    st.sidebar.caption(f"*(Solenoid Length 'L' automatically locked to {L_val} mm)*")
    
    t_cu_val = 0.2
    st.sidebar.caption(f"*(Bare Copper Thickness: {t_cu_val} mm)*")
    
    kapton_thou = st.sidebar.number_input("Kapton Tape Thickness (thou)", value=1.0, step=0.1)
    glue_thou = st.sidebar.number_input("Est. Glue Thickness (thou)", value=0.5, step=0.1)
    t_ins_mm = (kapton_thou + glue_thou) * 0.0254
    st.sidebar.caption(f"*(Total Insulator Thickness: {t_ins_mm:.4f} mm)*")
    
    t_layer_val = t_cu_val + t_ins_mm
    
    A_cu_val = foil_width * t_cu_val
    A_total_val = foil_width * t_layer_val
    
    # Foil Fill Factor (assuming 100% width utilization, it's just the thickness ratio)
    f_cu_default = A_cu_val / A_total_val

    # UI Labels for Foil
    lbl_cu_dim = "Bare Foil Thickness"
    val_cu_dim = t_cu_val
    cap_cu_dim = "Fixed 0.2 mm"
    
    lbl_tot_dim = "Total Layer Thickness"
    val_tot_dim = t_layer_val
    cap_tot_dim = f"{t_cu_val:.3f} mm + {t_ins_mm:.4f} mm"
    
    cap_area_cu = f"{foil_width} mm × {t_cu_val} mm"
    cap_area_tot = f"{foil_width} mm × {t_layer_val:.4f} mm"
    
    csv_conductor = f"{foil_width}mm Foil"
    csv_insulation = f"{kapton_thou + glue_thou} thou Kapton+Glue"

st.sidebar.markdown("---")
f_val = st.sidebar.number_input(
    "Bare Copper Fill Factor 'f'", 
    value=float(f_cu_default), 
    min_value=0.1, 
    max_value=1.0, 
    format="%.4f"
)
st.sidebar.caption(f"*(Theoretical max for this conductor: **{f_cu_default:.4f}**)*")

a_val = st.sidebar.number_input("Inner Radius 'a' (mm)", value=12.7)

# --- NEW: POWER DRIVE MODE ---
st.sidebar.markdown("---")
power_mode = st.sidebar.radio("Power Drive Mode", ["Constant Voltage (CV)", "Constant Current (CC)"])

if power_mode == "Constant Voltage (CV)":
    V_val = st.sidebar.number_input("Voltage (V)", value=12.0)
    I_val = None
    
    calc_mode = st.sidebar.radio("Coil Sizing Mode", ["By Current Density", "By Outer Radius"], index=1)
    if calc_mode == "By Current Density":
        j_val = st.sidebar.number_input("Current Density (A/mm²)", value=4.0)
        b_val = None
    else:
        b_val = st.sidebar.number_input("Outer Radius 'b' (mm)", value=31.5)
        j_val = None
else:
    I_val = st.sidebar.number_input("Constant Current (A)", value=5.0)
    V_val = None
    
    st.sidebar.info("💡 In Constant Current mode, current density is locked by your wire choice. Please define the coil size by Outer Radius.")
    b_val = st.sidebar.number_input("Outer Radius 'b' (mm)", value=31.5)
    calc_mode = "By Outer Radius"
    j_val = None

# --- CYCLOTRON SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Cyclotron Settings")

track_input_mode = st.sidebar.radio("Define Track By:", ["Radius", "Diameter"])
if track_input_mode == "Radius":
    track_r_val = st.sidebar.number_input("Track Radius (mm)", value=95.0)
    track_d_val = track_r_val * 2
else:
    track_d_val = st.sidebar.number_input("Track Diameter (mm)", value=190.0)
    track_r_val = track_d_val / 2

track_circ_val = np.pi * track_d_val

if track_input_mode == "Radius":
    st.sidebar.caption(f"*(Diameter: **{track_d_val:.1f}** mm | Circumference: **{track_circ_val:.1f}** mm)*")
else:
    st.sidebar.caption(f"*(Radius: **{track_r_val:.1f}** mm | Circumference: **{track_circ_val:.1f}** mm)*")

n_coils_val = st.sidebar.number_input("Number of Coils", value=6, min_value=1, step=1)

# --- SNUBBER SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Snubber Settings")
V_tvs_val = st.sidebar.number_input("TVS / Zener Voltage (V)", value=33.0)

st.sidebar.markdown("---")
st.sidebar.subheader("Projectile Settings")
r_ball_val = st.sidebar.number_input("Iron Ball Radius (mm)", value=6.0)
z0_val = st.sidebar.number_input("Switch Position z_0 (mm)", value=-12.0)

# --- THERMAL SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Thermal Settings")
h_conv_val = st.sidebar.number_input("Convection Coeff. h (W/m²·K)", value=10.0, step=1.0)
T_ambient_val = st.sidebar.number_input("Ambient Temp (°C)", value=20.0, step=1.0)


# --- UNIVERSAL CALCULATIONS ---
a = a_val * u.mm
L = L_val * u.mm
f = f_val
r_ball = r_ball_val * u.mm
z_0 = z0_val * u.mm
V_tvs = V_tvs_val * u.V

rho = 1.68e-8 * u.ohm * u.m
rho_cu = 8.96 * u.g / u.cm**3
rho_iron = 7874 * u.kg / u.m**3

A_cu = A_cu_val * u.mm**2
A_total = A_total_val * u.mm**2

# Core Universal Math Block
if power_mode == "Constant Voltage (CV)":
    V = V_val * u.V
    if calc_mode == "By Current Density":
        j = j_val * u.A / u.mm**2
        # Solve for b dynamically
        b = np.sqrt(a**2 + (V * A_total) / (j * rho * f * np.pi * L))
    else:
        b = b_val * u.mm
    
    # Universal Geometry
    l_bar = np.pi * (a + b)
    N = (f * L * (b - a)) / A_total
    total_length = N * l_bar
    R_coil = rho * total_length / A_cu
    
    I = V / R_coil
    j = I / A_cu
    P = (I * V).to(u.W)
    
else: # Constant Current (CC)
    I = I_val * u.A
    b = b_val * u.mm
    
    # Universal Geometry
    l_bar = np.pi * (a + b)
    N = (f * L * (b - a)) / A_total
    total_length = N * l_bar
    R_coil = rho * total_length / A_cu
    
    V = I * R_coil
    j = I / A_cu
    P = (I * V).to(u.W)

m_wire = rho_cu * A_cu * l_bar * N
NI = N * I


# --- 1. COIL GEOMETRY ---
st.header("1. Coil Geometry")
col1, col2, col3, col4 = st.columns(4)
col1.metric(lbl_cu_dim, f"{val_cu_dim:.3f} mm")
col1.caption(cap_cu_dim)

col2.metric(lbl_tot_dim, f"{val_tot_dim:.3f} mm")
col2.caption(cap_tot_dim)

col3.metric("Outer Radius (b)", f"{b.to(u.mm).magnitude:.2f} mm")
if power_mode == "Constant Voltage (CV)" and calc_mode == "By Current Density":
    col3.caption(f"√({a_val:.2f}² + ({V_val:.1f}V × {A_total_val:.4f}mm²) / ({j.to(u.A/u.mm**2).magnitude:.2f}A/mm² × 1.68e-8Ω·m × {f_val:.4f} × π × {L_val:.1f}mm))")
else:
    col3.caption("User Input")

col4.metric("Radial Build", f"{(b - a).to(u.mm).magnitude:.2f} mm")
col4.caption(f"{b.to(u.mm).magnitude:.2f} mm - {a_val:.2f} mm")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean Turn Length", f"{l_bar.to(u.mm).magnitude:.1f} mm")
col1.caption(f"π × ({a_val:.2f} mm + {b.to(u.mm).magnitude:.2f} mm)")

col2.metric("Number of Turns", f"{N.to(u.dimensionless).magnitude:.0f}")
col2.caption(f"({f_val:.4f} × {L_val:.1f} mm × {(b.to(u.mm).magnitude - a_val):.2f} mm) / {A_total_val:.4f} mm²")

col3.metric("Conductor Length", f"{total_length.to(u.m).magnitude:.0f} m")
col3.caption(f"{N.to(u.dimensionless).magnitude:.0f} turns × {l_bar.to(u.mm).magnitude:.1f} mm")

col4.metric("Cu Mass", f"{m_wire.to(u.g).magnitude:.0f} g")
col4.caption(f"8.96 g/cm³ × {A_cu.to(u.cm**2).magnitude:.5f} cm² × {total_length.to(u.cm).magnitude:.1f} cm")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Layer Area (with insul.)", f"{A_total_val:.4f} mm²")
col1.caption(cap_area_tot)


# --- 2. COIL ELECTRICAL ---
st.header("2. Coil Electrical")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Bare Cu Area", f"{A_cu_val:.4f} mm²")
col1.caption(cap_area_cu)

col2.metric("Resistance", f"{R_coil.to(u.ohm).magnitude:.2f} Ω")
col2.caption(f"1.68e-8 Ω·m × {total_length.to(u.m).magnitude:.2f} m / {A_cu_val:.4f} mm²")

# Dynamic UI swapping based on Power Mode
if power_mode == "Constant Voltage (CV)":
    col3.metric("Draw Current", f"{I.to(u.A).magnitude:.3f} A")
    col3.caption(f"{V_val:.1f} V / {R_coil.to(u.ohm).magnitude:.2f} Ω")
else:
    col3.metric("Req. Voltage", f"{V.to(u.V).magnitude:.2f} V")
    col3.caption(f"{I_val:.1f} A × {R_coil.to(u.ohm).magnitude:.2f} Ω")

col4.metric("Peak Power", f"{P.magnitude:.1f} W")
col4.caption(f"{I.to(u.A).magnitude:.3f} A × {V.to(u.V).magnitude:.2f} V")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Peak Current Density (j)", f"{j.to(u.A/u.mm**2).magnitude:.2f} A/mm²")
if power_mode == "Constant Voltage (CV)" and calc_mode == "By Current Density":
    col1.caption("User Input")
else:
    col1.caption(f"{I.to(u.A).magnitude:.3f} A / {A_cu_val:.4f} mm²")

col2.metric("Ampere-Turns (NI)", f"{NI.to(u.A).magnitude:.0f} AT")
col2.caption(f"{N.to(u.dimensionless).magnitude:.0f} turns × {I.to(u.A).magnitude:.3f} A")


# --- 3. CYCLOTRON SYSTEM & DUTY CYCLE ---
st.header("3. Cyclotron System & Duty Cycle")

dist_on_val = 2 * r_ball_val 
duty_cycle_decimal = dist_on_val / track_circ_val
duty_cycle_pct = duty_cycle_decimal * 100

P_avg = P * duty_cycle_decimal
P_sys_avg = P_avg * n_coils_val
j_rms = j * np.sqrt(duty_cycle_decimal)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Track Circumference", f"{track_circ_val:.1f} mm")
col1.caption(f"π × {track_d_val:.1f} mm")

col2.metric("Distance ON per cycle", f"{dist_on_val:.1f} mm")
col2.caption(f"2 × {r_ball_val:.1f} mm")

col3.metric("Indiv. Coil Duty Cycle", f"{duty_cycle_pct:.2f} %")
col3.caption(f"{dist_on_val:.1f} mm / {track_circ_val:.1f} mm")

col4.metric("Total System Duty Cycle", f"{duty_cycle_pct * n_coils_val:.2f} %")
col4.caption(f"{duty_cycle_pct:.2f}% × {n_coils_val} coils")


col1, col2, col3 = st.columns(3)
col1.metric("RMS Current Density (j_rms)", f"{j_rms.to(u.A/u.mm**2).magnitude:.2f} A/mm²")
col1.caption(f"{j.to(u.A/u.mm**2).magnitude:.2f} A/mm² × √({duty_cycle_decimal:.4f})")

col2.metric("Avg Power (Per Coil)", f"{P_avg.to(u.W).magnitude:.2f} W")
col2.caption(f"{P.magnitude:.1f} W × {duty_cycle_decimal:.4f}")

col3.metric("Avg Power (All Coils Combined)", f"{P_sys_avg.to(u.W).magnitude:.2f} W")
col3.caption(f"{P_avg.to(u.W).magnitude:.2f} W × {n_coils_val} coils")


# --- 4. THERMAL ANALYSIS & TEMPERATURE RISE ---
st.header("4. Thermal Analysis & Temperature Rise")

A_surface = (2 * np.pi * b * L) + (2 * np.pi * (b**2 - a**2))
A_surface_m2 = A_surface.to(u.m**2).magnitude
delta_T = P_avg.to(u.W).magnitude / (h_conv_val * A_surface_m2)
T_final = T_ambient_val + delta_T

col1, col2, col3, col4 = st.columns(4)
col1.metric("Exposed Surface Area", f"{A_surface.to(u.cm**2).magnitude:.1f} cm²")
col1.caption(f"Cylinder + Side Flanges")

col2.metric("Continuous Heat Load", f"{P_avg.to(u.W).magnitude:.2f} W")
col2.caption("Avg Power per coil")

col3.metric("Est. Temp Rise (ΔT)", f"{delta_T:.1f} °C")
col3.caption(f"{P_avg.to(u.W).magnitude:.2f} W / ({h_conv_val:.1f} W/m²·K × {A_surface_m2:.4f} m²)")

col4.metric("Est. Final Coil Temp", f"{T_final:.1f} °C")
col4.caption(f"{T_ambient_val:.1f} °C (Ambient) + {delta_T:.1f} °C")

st.info("💡 **Thermal Note:** This estimation assumes the coil is cooling via natural convection in still air. If the projectile or the rotating motion of the track creates localized airflow, the convection coefficient (h) will significantly increase, making the actual operating temperature even cooler than estimated here.")


# --- GLOBAL PLOT LIMITS & CALCS ---
L_mm = L.to(u.mm).magnitude
a_mm = a.to(u.mm).magnitude
b_mm = b.to(u.mm).magnitude
r_ball_mm = r_ball.to(u.mm).magnitude
z_0_mm = z_0.to(u.mm).magnitude
z_on_mag = (z_0 - r_ball).to(u.mm).magnitude
z_off_mag = (z_0 + r_ball).to(u.mm).magnitude

plot_x_min_val = -50.0
plot_x_max_val = 50.0


# --- 5. SPOOL, COIL & SENSOR VISUALIZATION ---
st.header("5. Spool, Coil & Sensor Visualization")

fig_geom, ax_geom = plt.subplots(figsize=(8, 5))

t_bobbin = 2.0  # mm

# Top flange
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2 - t_bobbin, a_mm - t_bobbin), t_bobbin, (b_mm - a_mm) + t_bobbin*2, facecolor='darkgray', edgecolor='black', label='Spool/Bobbin'))
ax_geom.add_patch(mpl.patches.Rectangle((L_mm/2, a_mm - t_bobbin), t_bobbin, (b_mm - a_mm) + t_bobbin*2, facecolor='darkgray', edgecolor='black'))
# Top tube
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2, a_mm - t_bobbin), L_mm, t_bobbin, facecolor='darkgray', edgecolor='black'))

# Bottom flange (mirror)
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2 - t_bobbin, -b_mm - t_bobbin), t_bobbin, (b_mm - a_mm) + t_bobbin*2, facecolor='darkgray', edgecolor='black'))
ax_geom.add_patch(mpl.patches.Rectangle((L_mm/2, -b_mm - t_bobbin), t_bobbin, (b_mm - a_mm) + t_bobbin*2, facecolor='darkgray', edgecolor='black'))
# Bottom tube (mirror)
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2, -a_mm), L_mm, t_bobbin, facecolor='darkgray', edgecolor='black'))

# Plot Coil Winding
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2, a_mm), L_mm, b_mm - a_mm, facecolor='peru', hatch='///', edgecolor='black', label='Copper Winding'))
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2, -b_mm), L_mm, b_mm - a_mm, facecolor='peru', hatch='///', edgecolor='black'))

# Add Iron Ball
ball = mpl.patches.Circle((z_0_mm, 0), r_ball_mm, facecolor='silver', edgecolor='black', linewidth=1.5, label='Iron Ball', zorder=3)
ax_geom.add_patch(ball)

# Sensor and Switch Boundaries
ax_geom.axvline(z_on_mag, color='green', linestyle='--', linewidth=1.5, label='Switch ON')
ax_geom.axvline(z_off_mag, color='orange', linestyle='--', linewidth=1.5, label='Switch OFF')
ax_geom.axvline(z_0_mm, color='black', linestyle=':', linewidth=1.5, label='Sensor Position')

# Center Axis
ax_geom.axhline(0, color='black', linestyle='-.', linewidth=1)

ax_geom.set_xlim(plot_x_min_val, plot_x_max_val)
ax_geom.set_ylim(-b_mm - 10, b_mm + 10)
ax_geom.set_aspect('equal')
ax_geom.set_xlabel('Length z (mm)')
ax_geom.set_ylabel('Radius r (mm)')
ax_geom.legend(loc='upper right', bbox_to_anchor=(1.35, 1))
ax_geom.grid(True, alpha=0.3)
ax_geom.set_title('Cross-Sectional View of Bobbin, Winding, and Projectile')

fig_geom.tight_layout()
st.pyplot(fig_geom)


# --- 6. BALL & MAGNETIC FIELD FUNCTIONS ---
def log_mean(rad_a, rad_b):
    return (rad_b - rad_a) / np.log(rad_b / rad_a)

def B_z(z, R, L, N, I):
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    z_plus = z + L / 2
    z_minus = z - L / 2
    term_plus = z_plus / np.sqrt(R**2 + z_plus**2)
    term_minus = z_minus / np.sqrt(R**2 + z_minus**2)
    return (mu_0 * N / L * I / 2) * (term_plus - term_minus)

def dBz_dz(z, R, L, N, I):
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    z_plus = z + L / 2
    z_minus = z - L / 2
    term_plus = R**2 / (R**2 + z_plus**2)**1.5
    term_minus = R**2 / (R**2 + z_minus**2)**1.5
    return (mu_0 * N / L * I / 2) * (term_plus - term_minus)

def F_z(z, R, L, N, I, r_ball):
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    V_ball = (4 / 3) * np.pi * r_ball**3
    B = B_z(z, R, L, N, I)
    dB = dBz_dz(z, R, L, N, I)
    return (3 * V_ball / (2 * mu_0)) * B * dB

def work_on_ball(z_0, r_ball, R, L, N, I):
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    V_ball = (4 / 3) * np.pi * r_ball**3
    z1 = z_0 - r_ball  
    z2 = z_0 + r_ball  
    B1 = B_z(z1, R, L, N, I)
    B2 = B_z(z2, R, L, N, I)
    return (3 * V_ball / (4 * mu_0)) * (B2**2 - B1**2)

R_eff = log_mean(a, b)
V_ball = (4 / 3) * np.pi * r_ball**3
m_ball = rho_iron * V_ball
v_0 = 0 * u.mm / u.s

B_0 = B_z(0*u.mm, R_eff, L, N, I)
B_on = B_z(z_0 - r_ball, R_eff, L, N, I)
B_off = B_z(z_0 + r_ball, R_eff, L, N, I)

W = work_on_ball(z_0, r_ball, R_eff, L, N, I)
KE_0 = 0.5 * m_ball * v_0**2
KE_f = KE_0 + W
v_f = np.sqrt(2 * KE_f / m_ball)

st.header("6. Iron Ball & Switch Configuration")
col1, col2, col3 = st.columns(3)
col1.metric("Ball Volume", f"{V_ball.to(u.mm**3).magnitude:.0f} mm³")
col1.caption(f"(4/3) × π × {r_ball_val:.1f}³ mm³")

col2.metric("Ball Mass", f"{m_ball.to(u.g).magnitude:.2f} g")
col2.caption(f"7.874 g/cm³ × {V_ball.to(u.cm**3).magnitude:.3f} cm³")

col3.metric("B at Center", f"{B_0.to(u.mT).magnitude:.1f} mT")
col3.caption("Biot-Savart field at z=0")

col1, col2, col3 = st.columns(3)
col1.metric("Field ON at z", f"{z_on_mag:.1f} mm")
col1.caption(f"{z0_val:.1f} mm - {r_ball_val:.1f} mm")

col2.metric("Field OFF at z", f"{z_off_mag:.1f} mm")
col2.caption(f"{z0_val:.1f} mm + {r_ball_val:.1f} mm")

col3.metric("Work done on ball", f"{W.to(u.mJ).magnitude:.2f} mJ")
col3.caption(f"∫ F_z dz ({z0_val - r_ball_val:.1f} to {z0_val + r_ball_val:.1f})")

st.markdown("### Performance After 1 Coil Kick")
rpm_1kick = (v_f.to(u.mm/u.s).magnitude / track_circ_val) * 60

col1, col2, col3, col4 = st.columns(4)
col1.metric("Initial Velocity", f"{v_0.to(u.mm/u.s).magnitude:.0f} mm/s")
col1.caption("Assumed 0 mm/s")

col2.metric("Velocity (1 Kick)", f"{v_f.to(u.mm/u.s).magnitude:.0f} mm/s")
col2.caption(f"√ (2 × {W.to(u.mJ).magnitude:.2f} mJ / {m_ball.to(u.g).magnitude:.2f} g)")

col3.metric("Velocity (km/h)", f"{v_f.to(u.km/u.h).magnitude:.2f} km/h")
col3.caption(f"{v_f.to(u.m/u.s).magnitude:.2f} m/s × 3.6")

col4.metric("Track Speed (RPM)", f"{rpm_1kick:.1f} RPM")
col4.caption(f"Based on {track_circ_val:.1f} mm track")

# --- FULL LAP PERFORMANCE ESTIMATION ---
st.markdown(f"### Performance After 1 Full Lap ({n_coils_val} Coils)")
W_lap = W * n_coils_val
KE_lap = KE_0 + W_lap
v_lap = np.sqrt(2 * KE_lap / m_ball)

freq_hz = v_lap.to(u.mm/u.s).magnitude / track_circ_val
rpm_lap = freq_hz * 60
period_ms = (1 / freq_hz) * 1000 if freq_hz > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Velocity (1 Lap)", f"{v_lap.to(u.m/u.s).magnitude:.2f} m/s")
col1.caption(f"√ (2 × {W_lap.to(u.mJ).magnitude:.2f} mJ / {m_ball.to(u.g).magnitude:.2f} g)")

col2.metric("Track Frequency", f"{freq_hz:.2f} Hz")
col2.caption("Laps per second")

col3.metric("Track Speed (RPM)", f"{rpm_lap:.1f} RPM")
col3.caption(f"{freq_hz:.2f} Hz × 60")

col4.metric("Lap Period", f"{period_ms:.1f} ms")
col4.caption(f"1 / {freq_hz:.2f} Hz")


# --- 7. INDUCTANCE & STORED ENERGY ---
def nagaoka_coefficient(R, L):
    k = 2 * R / L 
    K = 1 / (1 + 0.9 * R / L - 0.02 * (R / L)**2 + 0.01 * (R / L)**3)
    return K.to(u.dimensionless).magnitude

def solenoid_inductance(N, R, L):
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    K = nagaoka_coefficient(R, L)
    return mu_0 * N**2 * np.pi * R**2 * K / L

L_coil = solenoid_inductance(N, R_eff, L)
tau = L_coil / R_coil
E_stored = 0.5 * L_coil * I**2
t_on = (2 * r_ball / v_f).to(u.ms)

# Calculate Wake-Up speed limits
t_99 = 5 * tau
v_choke = (2 * r_ball / t_99).to(u.m / u.s)
rpm_choke = (v_choke.to(u.mm/u.s).magnitude / track_circ_val) * 60

st.header("7. Inductance & Time Constant")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Nagaoka Coeff (K)", f"{nagaoka_coefficient(R_eff, L):.2f}")
col1.caption(f"f(R_eff={R_eff.to(u.mm).magnitude:.1f}mm, L={L_val:.1f}mm)")

col2.metric("Inductance", f"{L_coil.to(u.mH).magnitude:.1f} mH")
col2.caption(f"(μ₀ × {N.to(u.dimensionless).magnitude:.0f}² × π × {R_eff.to(u.mm).magnitude:.1f}² × {nagaoka_coefficient(R_eff, L):.2f}) / {L_val:.1f} mm")

col3.metric("Time Constant (τ)", f"{tau.to(u.ms).magnitude:.1f} ms")
col3.caption(f"{L_coil.to(u.mH).magnitude:.2f} mH / {R_coil.to(u.ohm).magnitude:.2f} Ω")

col4.metric("Stored Energy", f"{E_stored.to(u.mJ).magnitude:.1f} mJ")
col4.caption(f"½ × {L_coil.to(u.mH).magnitude:.2f} mH × ({I.to(u.A).magnitude:.3f} A)²")


st.markdown("### Coil Wake-Up & Speed Limit Analysis")
col1, col2, col3, col4 = st.columns(4)
col1.metric("99% Rise Time (5τ)", f"{t_99.to(u.ms).magnitude:.2f} ms")
col1.caption("Time to reach full magnetic force")

col2.metric("Est. Sensor ON-Time (Lap 1)", f"{t_on.to(u.ms).magnitude:.2f} ms")
col2.caption(f"At {v_f.to(u.m/u.s).magnitude:.2f} m/s")

col3.metric("Max Speed Before Choking", f"{v_choke.to(u.m/u.s).magnitude:.2f} m/s")
col3.caption(f"Speed where ON-time equals {t_99.to(u.ms).magnitude:.2f} ms")

col4.metric("Max Limit (RPM)", f"{rpm_choke:.0f} RPM")
col4.caption("Absolute track RPM limit")

if t_99 > t_on:
    st.warning(f"⚠️ **Wake-Up Too Slow:** The coil takes longer to fully turn on ({t_99.to(u.ms).magnitude:.2f} ms) than the ball spends in the sensor zone ({t_on.to(u.ms).magnitude:.2f} ms). You are losing pulling power on the very first kick!")
else:
    st.success(f"✅ **Wake-Up Speed Good:** The coil fully magnetizes ({t_99.to(u.ms).magnitude:.2f} ms) before the ball leaves the sensor zone ({t_on.to(u.ms).magnitude:.2f} ms) on the first kick.")


# --- 8. MAGNETIC FIELD PLOT ---
st.header("8. On-axis Magnetic Field Profile")

z_vals_field = np.linspace(plot_x_min_val, plot_x_max_val, 400) * u.mm
z_plot_mm = z_vals_field.m_as(u.mm)
B_plot = B_z(z_vals_field, R_eff, L, N, I).m_as(u.mT)

fig_field, ax1 = plt.subplots(figsize=(8, 5))

ax1.plot(z_plot_mm, B_plot, 'b-', linewidth=2, label='$B_z$')
ax1.axvline(z_0.m_as(u.mm), color='k', linestyle=':', label='Sensor')
ax1.axvspan(-L.m_as(u.mm)/2, L.m_as(u.mm)/2, color='k', alpha=0.2, label='Solenoid extent')

ax1.set_xlim(plot_x_min_val, plot_x_max_val)
ax1.set_xlabel('z (mm)')
ax1.set_ylabel('$B_z$ (mT)')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_title('On-axis magnetic field')

fig_field.tight_layout()
st.pyplot(fig_field)


# --- 9. COMBINED PLOTTING ---
st.header("9. Combined Field and Force Profiles")

z_vals = np.linspace(plot_x_min_val, plot_x_max_val, 400) * u.mm

B_vals = B_z(z_vals, R_eff, L, N, I).to(u.mT).magnitude
F_vals = F_z(z_vals, R_eff, L, N, I, r_ball).to(u.mN).magnitude

fig, ax1 = plt.subplots(figsize=(10, 5))

ax1.set_xlabel('Position z (mm)')
ax1.set_ylabel('Magnetic Field B_z (mT)', color='tab:blue')
ax1.plot(z_vals.magnitude, B_vals, color='tab:blue', label='B_z')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, alpha=0.3)

ax1.axvspan(z_on_mag, z_off_mag, color='orange', alpha=0.2, label='Coil ON Region (Work Integration)')

ax2 = ax1.twinx()
ax2.set_ylabel('Axial Force F_z (mN)', color='tab:red')
ax2.plot(z_vals.magnitude, F_vals, color='tab:red', linestyle='--', label='F_z')
ax2.tick_params(axis='y', labelcolor='tab:red')

ax1.set_xlim(plot_x_min_val, plot_x_max_val)
fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9), bbox_transform=ax1.transAxes)
fig.tight_layout()
st.pyplot(fig)


# --- 10. SNUBBER EFFECT & SUCK-BACK ANALYSIS ---
st.header("10. Snubber Effect & Suck-Back Analysis (Force Decay)")

z_sb = np.linspace(plot_x_min_val, plot_x_max_val, 400) * u.mm

# Calculate ratio of current decay over time, mapped to space via velocity
I_ratio_ideal = np.zeros(len(z_sb))
I_ratio_flyback = np.zeros(len(z_sb))
I_ratio_zener = np.zeros(len(z_sb))

for i, z_val in enumerate(z_sb):
    z_m = z_val.to(u.mm).magnitude
    if z_on_mag <= z_m <= z_off_mag:
        I_ratio_ideal[i] = 1.0
        I_ratio_flyback[i] = 1.0
        I_ratio_zener[i] = 1.0
    elif z_m > z_off_mag:
        # Time since switch turned off
        dt = (z_val - (z_0 + r_ball)) / v_f
        
        # 1. Flyback decay: I(t) = I0 * e^(-t/tau)
        decay_fb = np.exp(-dt / tau).to(u.dimensionless).magnitude
        I_ratio_flyback[i] = decay_fb
        
        # 2. TVS / Zener decay: I(t) = (I0 + Vz/R) * e^(-t/tau) - Vz/R
        I_0_val = I
        I_z_decay = ((I_0_val + V_tvs / R_coil) * np.exp(-dt / tau) - V_tvs / R_coil) / I_0_val
        I_ratio_zener[i] = max(0.0, I_z_decay.to(u.dimensionless).magnitude)

# Because Force is proportional to I^2, we calculate base force and scale it
F_base = F_z(z_sb, R_eff, L, N, I, r_ball).to(u.mN).magnitude

F_ideal = F_base * (I_ratio_ideal**2)
F_flyback = F_base * (I_ratio_flyback**2)
F_zener = F_base * (I_ratio_zener**2)

fig_sb, ax_sb = plt.subplots(figsize=(10, 5))

ax_sb.plot(z_sb.magnitude, F_ideal, 'g--', label='Ideal Switch (Instant Cutoff)', linewidth=2)
ax_sb.plot(z_sb.magnitude, F_flyback, 'r-', label='Standard Flyback Diode (Slow Decay)', linewidth=2)
ax_sb.plot(z_sb.magnitude, F_zener, 'b-', label=f'TVS Snubber ({V_tvs_val}V)', linewidth=2)

# Highlight suck-back region
ax_sb.axhspan(-max(abs(F_base)), 0, color='red', alpha=0.05, label='Suck-Back Region (Deceleration)')
ax_sb.axvline(0, color='k', linestyle=':', label='Coil Center')

# Switch ON/OFF lines
ax_sb.axvline(z_on_mag, color='g', linestyle='--', label='Switch ON')
ax_sb.axvline(z_off_mag, color='orange', linestyle='--', label='Switch OFF')

ax_sb.set_xlim(plot_x_min_val, plot_x_max_val)
ax_sb.set_xlabel('Position z (mm)')
ax_sb.set_ylabel('Axial Force F_z (mN)')
ax_sb.legend(loc='upper right')
ax_sb.grid(True, alpha=0.3)
ax_sb.set_title('Force Profile Decay & Suck-Back Effect (Mapped via Final Velocity)')

fig_sb.tight_layout()
st.pyplot(fig_sb)

st.info("💡 **Understanding Suck-Back:** The force naturally becomes negative (pulling backwards) after the ball crosses the exact center of the coil ($z = 0$). If the coil's current decays too slowly (red line), the coil stays magnetized as the ball passes the center, dragging it backwards and stealing the kinetic energy you just added. The TVS Snubber (blue line) forces the current to zero much faster, virtually eliminating this deceleration drag.")


# --- CSV EXPORT GENERATION ---
st.sidebar.markdown("---")
st.sidebar.subheader("Export Data")

export_data = {
    "Parameter": [
        "Power Drive Mode", "Conductor Type", "Insulation", "Fill Factor", "Req/Set Voltage (V)", "Coil Length L (mm)", "Inner Radius a (mm)", "Outer Radius b (mm)",
        "Bare Cu Thickness/Dia (mm)", "Total Layer/Wire Thickness (mm)", "Radial Build (mm)", "Mean Turn Length (mm)", "Number of Turns", "Conductor Length (m)", "Cu Mass (g)",
        "Bare Cu Area (mm²)", "Total Layer Area (mm²)", "Resistance (Ω)", "Peak Current (A)", "Peak Power (W)", "Current Density (A/mm²)", "Ampere-Turns (AT)",
        "Track Circumference (mm)", "System Coils", "Dist. ON Per Cycle (mm)", "Coil Duty Cycle (%)", "System Duty Cycle (%)", "RMS Current Density (A/mm²)", "Avg Power Per Coil (W)", "Avg Power System (W)",
        "Exposed Area (cm²)", "Est. Temp Rise (°C)", "Est. Final Temp (°C)",
        "Ball Radius (mm)", "Ball Mass (g)", "Switch Position z_0 (mm)", "Max Force B_z at Center (mT)", "Work Done on Ball (mJ)", "Velocity (1 Kick) (m/s)", "Track Speed 1-Kick (RPM)",
        "Velocity (1 Lap) (m/s)", "Track Frequency (Hz)", "Track Speed 1-Lap (RPM)", "Lap Period (ms)",
        "Inductance (mH)", "Time Constant τ (ms)", "99% Rise Time 5τ (ms)", "Stored Energy (mJ)", "Max Speed Before Choke (RPM)"
    ],
    "Value": [
        power_mode, csv_conductor, csv_insulation, f_val, V.to(u.V).magnitude, L_val, a_val, b.to(u.mm).magnitude,
        val_cu_dim, val_tot_dim, (b - a).to(u.mm).magnitude, l_bar.to(u.mm).magnitude, N.to(u.dimensionless).magnitude, total_length.to(u.m).magnitude, m_wire.to(u.g).magnitude,
        A_cu_val, A_total_val, R_coil.to(u.ohm).magnitude, I.to(u.A).magnitude, P.magnitude, j.to(u.A/u.mm**2).magnitude, NI.to(u.A).magnitude,
        track_circ_val, n_coils_val, dist_on_val, duty_cycle_pct, (duty_cycle_pct * n_coils_val), j_rms.to(u.A/u.mm**2).magnitude, P_avg.to(u.W).magnitude, P_sys_avg.to(u.W).magnitude,
        A_surface.to(u.cm**2).magnitude, delta_T, T_final,
        r_ball_val, m_ball.to(u.g).magnitude, z0_val, B_0.to(u.mT).magnitude, W.to(u.mJ).magnitude, v_f.to(u.m/u.s).magnitude, rpm_1kick,
        v_lap.to(u.m/u.s).magnitude, freq_hz, rpm_lap, period_ms,
        L_coil.to(u.mH).magnitude, tau.to(u.ms).magnitude, t_99.to(u.ms).magnitude, E_stored.to(u.mJ).magnitude, rpm_choke
    ]
}

df_export = pd.DataFrame(export_data)
csv_export = df_export.to_csv(index=False).encode('utf-8')

st.sidebar.download_button(
    label="Download Full Specs as CSV",
    data=csv_export,
    file_name="cyclotron_coil_specs.csv",
    mime="text/csv",
)
