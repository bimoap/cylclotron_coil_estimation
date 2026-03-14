import streamlit as st
import numpy as np
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

awg = st.sidebar.number_input("Wire AWG", min_value=1, max_value=40, value=20, step=1)

# Enamel Thickness Input (thou to mm conversion)
t_enamel_thou = st.sidebar.number_input("Enamel Thickness (thou)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
t_enamel_mm = t_enamel_thou * 0.0254
st.sidebar.caption(f"*(Metric equivalent: {t_enamel_mm:.4f} mm)*")

# Calculate Dynamic Default for Fill Factor
d_cu_val = awg_diameter(awg)
d_total_val = d_cu_val + (2 * t_enamel_mm)

# Orthocyclic limit = pi / (2 * sqrt(3)) ≈ 0.9069
geom_limit = np.pi / (2 * np.sqrt(3))
# Copper Space Factor scales the geometric limit by the bare-to-total area ratio
f_cu_default = geom_limit * ((d_cu_val / d_total_val) ** 2)

f_val = st.sidebar.number_input(
    "Copper Fill Factor 'f'", 
    value=float(f_cu_default), 
    min_value=0.1, 
    max_value=1.0, 
    format="%.4f"
)
st.sidebar.caption(f"*(Theoretical orthocyclic max for AWG {awg}: **{f_cu_default:.4f}**)*")

V_val = st.sidebar.number_input("Voltage (V)", value=12.0)
a_val = st.sidebar.number_input("Inner Radius 'a' (mm)", value=12.7)
L_val = st.sidebar.number_input("Solenoid Length 'L' (mm)", value=20.0)

# --- NEW: CALCULATION MODE ---
st.sidebar.markdown("---")
calc_mode = st.sidebar.radio("Calculation Mode", ["By Current Density", "By Outer Radius"], index=1)

if calc_mode == "By Current Density":
    j_val = st.sidebar.number_input("Current Density (A/mm²)", value=4.0)
    b_val = None
else:
    b_val = st.sidebar.number_input("Outer Radius 'b' (mm)", value=31.5)
    j_val = None

# --- CYCLOTRON SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Cyclotron Settings")
track_circ_val = st.sidebar.number_input("Track Circumference (mm)", value=596.9026, format="%.4f")
n_coils_val = st.sidebar.number_input("Number of Coils", value=6, min_value=1, step=1)

# --- SNUBBER SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Snubber Settings")
V_tvs_val = st.sidebar.number_input("TVS / Zener Voltage (V)", value=33.0)

st.sidebar.markdown("---")
st.sidebar.subheader("Projectile Settings")
r_ball_val = st.sidebar.number_input("Iron Ball Radius (mm)", value=6.0)
z0_val = st.sidebar.number_input("Switch Position z_0 (mm)", value=-12.0)

# --- APPLY UNITS & CONSTANTS ---
V = V_val * u.V
a = a_val * u.mm
L = L_val * u.mm
f = f_val
r_ball = r_ball_val * u.mm
z_0 = z0_val * u.mm
t_enamel = t_enamel_mm * u.mm
V_tvs = V_tvs_val * u.V

rho = 1.68e-8 * u.ohm * u.m  # copper resistivity
rho_cu = 8.96 * u.g / u.cm**3
rho_iron = 7874 * u.kg / u.m**3

# --- WIRE GEOMETRY WITH ENAMEL ---
d_cu = d_cu_val * u.mm
d_total = d_total_val * u.mm

A_cu = np.pi * (d_cu / 2) ** 2             
A_total = np.pi * (d_total / 2) ** 2       

# --- CORE CALCULATION BASED ON SELECTED MODE ---
if calc_mode == "By Current Density":
    j = j_val * u.A / u.mm**2
    # Calculate outer radius b
    b = np.sqrt(a**2 + (V * A_total) / (j * rho * f * np.pi * L))
else:
    b = b_val * u.mm
    # Calculate current density j based on chosen b
    j_raw = (V * A_total) / ((b**2 - a**2) * rho * f * np.pi * L)
    j = j_raw.to(u.A / u.mm**2)

# --- DERIVED QUANTITIES ---
l_bar = np.pi * (a + b)
N = V / (j * rho * l_bar)
I = j * A_cu                               
NI = N * I                                 
total_length = N * l_bar
R_coil = rho * total_length / A_cu         
P = (I * V).to(u.W)
m_wire = rho_cu * A_cu * l_bar * N         


# --- 1. COIL GEOMETRY ---
st.header("1. Coil Geometry")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Bare Cu Diameter", f"{d_cu.to(u.mm).magnitude:.3f} mm")
col1.caption(f"0.127 × 92^((36-{awg})/39)")

col2.metric("Total Wire Dia.", f"{d_total.to(u.mm).magnitude:.3f} mm")
col2.caption(f"{d_cu.to(u.mm).magnitude:.3f} mm + 2({t_enamel_mm:.4f} mm)")

col3.metric("Outer Radius (b)", f"{b.to(u.mm).magnitude:.2f} mm")
if calc_mode == "By Current Density":
    col3.caption(f"√({a_val:.2f}² + ({V_val:.1f}V × {A_total.to(u.mm**2).magnitude:.4f}mm²) / ({j.to(u.A/u.mm**2).magnitude:.2f}A/mm² × 1.68e-8Ω·m × {f_val:.4f} × π × {L_val:.1f}mm))")
else:
    col3.caption("User Input")

col4.metric("Radial Build", f"{(b - a).to(u.mm).magnitude:.2f} mm")
col4.caption(f"{b.to(u.mm).magnitude:.2f} mm - {a_val:.2f} mm")


col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean Turn Length", f"{l_bar.to(u.mm).magnitude:.1f} mm")
col1.caption(f"π × ({a_val:.2f} mm + {b.to(u.mm).magnitude:.2f} mm)")

col2.metric("Number of Turns", f"{N.to(u.dimensionless).magnitude:.0f}")
col2.caption(f"({f_val:.4f} × {L_val:.1f} mm × {(b.to(u.mm).magnitude - a_val):.2f} mm) / {A_total.to(u.mm**2).magnitude:.4f} mm²")

col3.metric("Wire Length", f"{total_length.to(u.m).magnitude:.0f} m")
col3.caption(f"{N.to(u.dimensionless).magnitude:.0f} turns × {l_bar.to(u.mm).magnitude:.1f} mm")

col4.metric("Cu Wire Mass", f"{m_wire.to(u.g).magnitude:.0f} g")
col4.caption(f"8.96 g/cm³ × {A_cu.to(u.cm**2).magnitude:.5f} cm² × {total_length.to(u.cm).magnitude:.1f} cm")


# --- 2. COIL ELECTRICAL ---
st.header("2. Coil Electrical")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Resistance", f"{R_coil.to(u.ohm).magnitude:.2f} Ω")
col1.caption(f"1.68e-8 Ω·m × {total_length.to(u.m).magnitude:.2f} m / {A_cu.to(u.mm**2).magnitude:.4f} mm²")

col2.metric("Current", f"{I.to(u.A).magnitude:.3f} A")
col2.caption(f"{V_val:.1f} V / {R_coil.to(u.ohm).magnitude:.2f} Ω")

col3.metric("Peak Power", f"{P.magnitude:.1f} W")
col3.caption(f"{I.to(u.A).magnitude:.3f} A × {V_val:.1f} V")

col4.metric("Peak Current Density (j)", f"{j.to(u.A/u.mm**2).magnitude:.2f} A/mm²")
if calc_mode == "By Current Density":
    col4.caption("User Input")
else:
    col4.caption(f"({V_val:.1f}V × {A_total.to(u.mm**2).magnitude:.4f}mm²) / (({b_val:.2f}² - {a_val:.2f}²) × 1.68e-8Ω·m × {f_val:.4f} × π × {L_val:.1f}mm)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ampere-Turns (NI)", f"{NI.to(u.A).magnitude:.0f} AT")
col1.caption(f"{N.to(u.dimensionless).magnitude:.0f} turns × {I.to(u.A).magnitude:.3f} A")


# --- 3. SPOOL & COIL VISUALIZATION ---
st.header("3. Spool & Coil Geometry Visualization")

fig_geom, ax_geom = plt.subplots(figsize=(8, 5))

L_mm = L.to(u.mm).magnitude
a_mm = a.to(u.mm).magnitude
b_mm = b.to(u.mm).magnitude

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

# Center Axis
ax_geom.axhline(0, color='black', linestyle='-.', linewidth=1, label='Center Axis')

ax_geom.set_xlim(-L_mm/2 - 10, L_mm/2 + 10)
ax_geom.set_ylim(-b_mm - 10, b_mm + 10)
ax_geom.set_aspect('equal')
ax_geom.set_xlabel('Length z (mm)')
ax_geom.set_ylabel('Radius r (mm)')
ax_geom.legend(loc='upper right', bbox_to_anchor=(1.35, 1))
ax_geom.grid(True, alpha=0.3)
ax_geom.set_title('Cross-Sectional View of Bobbin and Winding')

fig_geom.tight_layout()
st.pyplot(fig_geom)


# --- 4. BALL & MAGNETIC FIELD FUNCTIONS ---
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

st.header("4. Iron Ball & Switch Configuration")
col1, col2, col3 = st.columns(3)
col1.metric("Ball Volume", f"{V_ball.to(u.mm**3).magnitude:.0f} mm³")
col1.caption(f"(4/3) × π × {r_ball_val:.1f}³ mm³")

col2.metric("Ball Mass", f"{m_ball.to(u.g).magnitude:.2f} g")
col2.caption(f"7.874 g/cm³ × {V_ball.to(u.cm**3).magnitude:.3f} cm³")

col3.metric("B at Center", f"{B_0.to(u.mT).magnitude:.1f} mT")
col3.caption("Biot-Savart field at z=0")


col1, col2, col3 = st.columns(3)
col1.metric("Field ON at z", f"{(z_0 - r_ball).to(u.mm).magnitude:.1f} mm")
col1.caption(f"{z0_val:.1f} mm - {r_ball_val:.1f} mm")

col2.metric("Field OFF at z", f"{(z_0 + r_ball).to(u.mm).magnitude:.1f} mm")
col2.caption(f"{z0_val:.1f} mm + {r_ball_val:.1f} mm")

col3.metric("Work done on ball", f"{W.to(u.mJ).magnitude:.2f} mJ")
col3.caption(f"∫ F_z dz ({z0_val - r_ball_val:.1f} to {z0_val + r_ball_val:.1f})")


col1, col2, col3 = st.columns(3)
col1.metric("Initial Velocity", f"{v_0.to(u.mm/u.s).magnitude:.0f} mm/s")
col1.caption("Assumed 0 mm/s")

col2.metric("Final Velocity", f"{v_f.to(u.mm/u.s).magnitude:.0f} mm/s")
col2.caption(f"√ (2 × {W.to(u.mJ).magnitude:.2f} mJ / {m_ball.to(u.g).magnitude:.2f} g)")

col3.metric("Final Velocity (km/h)", f"{v_f.to(u.km/u.h).magnitude:.2f} km/h")
col3.caption(f"{v_f.to(u.m/u.s).magnitude:.2f} m/s × 3.6")


# --- 5. CYCLOTRON SYSTEM & DUTY CYCLE ---
st.header("5. Cyclotron System & Duty Cycle")

dist_on_val = 2 * r_ball_val 
duty_cycle_decimal = dist_on_val / track_circ_val
duty_cycle_pct = duty_cycle_decimal * 100

P_avg = P * duty_cycle_decimal
P_sys_avg = P_avg * n_coils_val
j_rms = j * np.sqrt(duty_cycle_decimal)

col1, col2, col3 = st.columns(3)
col1.metric("Distance ON per cycle", f"{dist_on_val:.1f} mm")
col1.caption(f"2 × {r_ball_val:.1f} mm")

col2.metric("Individual Coil Duty Cycle", f"{duty_cycle_pct:.2f} %")
col2.caption(f"{dist_on_val:.1f} mm / {track_circ_val:.4f} mm")

col3.metric("Total System Duty Cycle", f"{duty_cycle_pct * n_coils_val:.2f} %")
col3.caption(f"{duty_cycle_pct:.2f}% × {n_coils_val} coils")


col1, col2, col3 = st.columns(3)
col1.metric("RMS Current Density (j_rms)", f"{j_rms.to(u.A/u.mm**2).magnitude:.2f} A/mm²")
col1.caption(f"{j.to(u.A/u.mm**2).magnitude:.2f} A/mm² × √({duty_cycle_decimal:.4f})")

col2.metric("Avg Power (Per Coil)", f"{P_avg.to(u.W).magnitude:.2f} W")
col2.caption(f"{P.magnitude:.1f} W × {duty_cycle_decimal:.4f}")

col3.metric("Avg Power (All Coils Combined)", f"{P_sys_avg.to(u.W).magnitude:.2f} W")
col3.caption(f"{P_avg.to(u.W).magnitude:.2f} W × {n_coils_val} coils")


# --- 6. INDUCTANCE ---
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
t_on = (2 * r_ball / v_f).to(u.ms)

st.header("6. Inductance & Time Constant")
col1, col2, col3 = st.columns(3)
col1.metric("Nagaoka Coeff (K)", f"{nagaoka_coefficient(R_eff, L):.2f}")
col1.caption(f"f(R_eff={R_eff.to(u.mm).magnitude:.1f}mm, L={L_val:.1f}mm)")

col2.metric("Inductance", f"{L_coil.to(u.mH).magnitude:.1f} mH")
col2.caption(f"(μ₀ × {N.to(u.dimensionless).magnitude:.0f}² × π × {R_eff.to(u.mm).magnitude:.1f}² × {nagaoka_coefficient(R_eff, L):.2f}) / {L_val:.1f} mm")

col3.metric("Time Constant (τ)", f"{tau.to(u.ms).magnitude:.1f} ms")
col3.caption(f"{L_coil.to(u.mH).magnitude:.2f} mH / {R_coil.to(u.ohm).magnitude:.2f} Ω")

st.write(f"**Estimated ON time (First kick):** {t_on.magnitude:.4f} ms")
st.caption(f"2 × {r_ball_val:.1f} mm / {v_f.to(u.mm/u.s).magnitude:.0f} mm/s")


# --- 7. MAGNETIC FIELD PLOT ---
st.header("7. On-axis Magnetic Field Profile")

z_vals_field = np.linspace(-L_val * 2.5, L_val * 2.5, 300) * u.mm
z_plot_mm = z_vals_field.m_as(u.mm)
B_plot = B_z(z_vals_field, R_eff, L, N, I).m_as(u.mT)

fig_field, ax1 = plt.subplots(figsize=(8, 5))

ax1.plot(z_plot_mm, B_plot, 'b-', linewidth=2, label='$B_z$')
ax1.axvline(z_0.m_as(u.mm), color='k', linestyle=':', label='Sensor')
ax1.axvspan(-L.m_as(u.mm)/2, L.m_as(u.mm)/2, color='k', alpha=0.2, label='Solenoid extent')

ax1.set_xlabel('z (mm)')
ax1.set_ylabel('$B_z$ (mT)')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_title('On-axis magnetic field')

fig_field.tight_layout()
st.pyplot(fig_field)


# --- 8. COMBINED PLOTTING ---
st.header("8. Combined Field and Force Profiles")

z_vals = np.linspace(-L_val*2, L_val*2, 200) * u.mm

B_vals = B_z(z_vals, R_eff, L, N, I).to(u.mT).magnitude
F_vals = F_z(z_vals, R_eff, L, N, I, r_ball).to(u.mN).magnitude

fig, ax1 = plt.subplots(figsize=(10, 5))

ax1.set_xlabel('Position z (mm)')
ax1.set_ylabel('Magnetic Field B_z (mT)', color='tab:blue')
ax1.plot(z_vals.magnitude, B_vals, color='tab:blue', label='B_z')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, alpha=0.3)

z_on_mag = (z_0 - r_ball).to(u.mm).magnitude
z_off_mag = (z_0 + r_ball).to(u.mm).magnitude
ax1.axvspan(z_on_mag, z_off_mag, color='orange', alpha=0.2, label='Coil ON Region (Work Integration)')

ax2 = ax1.twinx()
ax2.set_ylabel('Axial Force F_z (mN)', color='tab:red')
ax2.plot(z_vals.magnitude, F_vals, color='tab:red', linestyle='--', label='F_z')
ax2.tick_params(axis='y', labelcolor='tab:red')

fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9), bbox_transform=ax1.transAxes)
fig.tight_layout()
st.pyplot(fig)


# --- 9. SNUBBER EFFECT & SUCK-BACK ANALYSIS ---
st.header("9. Snubber Effect & Suck-Back Analysis (Force Decay)")

# Generate positions specifically showing the switch-off region and beyond
z_sb = np.linspace(-L_val * 1.5, L_val * 2.5, 400) * u.mm
z_on_mag = (z_0 - r_ball).to(u.mm).magnitude
z_off_mag = (z_0 + r_ball).to(u.mm).magnitude

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
ax_sb.axvline(z_off_mag, color='orange', linestyle='--', label='Switch OFF')

ax_sb.set_xlabel('Position z (mm)')
ax_sb.set_ylabel('Axial Force F_z (mN)')
ax_sb.legend(loc='upper right')
ax_sb.grid(True, alpha=0.3)
ax_sb.set_title('Force Profile Decay & Suck-Back Effect (Mapped via Final Velocity)')

fig_sb.tight_layout()
st.pyplot(fig_sb)

st.info("💡 **Understanding Suck-Back:** The force naturally becomes negative (pulling backwards) after the ball crosses the exact center of the coil ($z = 0$). If the coil's current decays too slowly (red line), the coil stays magnetized as the ball passes the center, dragging it backwards and stealing the kinetic energy you just added. The TVS Snubber (blue line) forces the current to zero much faster, virtually eliminating this deceleration drag.")


# --- 10. SOLENOID SYSTEM CROSS-SECTION PLOT ---
st.header("10. Solenoid System Cross-Section")

fig2, ax3 = plt.subplots(figsize=(8, 5))

r_ball_mm = r_ball.to(u.mm).magnitude
z_0_mm = z_0.to(u.mm).magnitude

# Upper coil cross-section
coil_upper = mpl.patches.Rectangle((-L_mm / 2, a_mm), L_mm, b_mm - a_mm, facecolor='orange', edgecolor='black', linewidth=1.5, label='Coil')
ax3.add_patch(coil_upper)

# Lower coil cross-section
coil_lower = mpl.patches.Rectangle((-L_mm / 2, -b_mm), L_mm, b_mm - a_mm, facecolor='orange', edgecolor='black', linewidth=1.5)
ax3.add_patch(coil_lower)

# Iron ball
ball = mpl.patches.Circle((z_0_mm, 0), r_ball_mm, facecolor='gray', edgecolor='black', linewidth=1.5, label='Iron ball')
ax3.add_patch(ball)

ax3.axvline(z_on_mag, color='g', linestyle='--', label='Field on')
ax3.axvline(z_off_mag, color='r', linestyle='--', label='Field off')
ax3.axvline(z_0.m_as(u.mm), color='k', linestyle=':', label='Sensor')
ax3.axhline(0, color='k', linestyle='-', linewidth=0.5)

ax3.set_xlim(-50, 50)
ax3.set_ylim(-30, 30)
ax3.set_aspect('equal')
ax3.set_xlabel('z (mm)')
ax3.set_ylabel('r (mm)')
ax3.legend(loc='upper right')
ax3.grid(True, alpha=0.3)
ax3.set_title('System cross-section including ball and sensors (to scale)')

fig2.tight_layout()
st.pyplot(fig2)
