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

awg = st.sidebar.number_input("Wire AWG", min_value=1, max_value=40, value=28, step=1)

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
calc_mode = st.sidebar.radio("Calculation Mode", ["By Current Density", "By Outer Radius"])

if calc_mode == "By Current Density":
    j_val = st.sidebar.number_input("Current Density (A/mm²)", value=4.0)
    b_val = None
else:
    b_val = st.sidebar.number_input("Outer Radius 'b' (mm)", value=28.0)
    j_val = None

# --- NEW: CYCLOTRON SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Cyclotron Settings")
track_circ_val = st.sidebar.number_input("Track Circumference (mm)", value=596.9026, format="%.4f")
n_coils_val = st.sidebar.number_input("Number of Coils", value=6, min_value=1, step=1)

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
    # Rearranged from: b^2 = a^2 + (V * A_total) / (j * rho * f * pi * L)
    j_raw = (V * A_total) / ((b**2 - a**2) * rho * f * np.pi * L)
    j = j_raw.to(u.A / u.mm**2)

# --- DERIVED QUANTITIES ---
l_bar = np.pi * (a + b)
N = V / (j * rho * l_bar)
I = j * A_cu                               # Current is driven through bare copper
NI = N * I                                 # Ampere-Turns
total_length = N * l_bar
P = (I * V).to(u.W)
m_wire = rho_cu * A_cu * l_bar * N         # Mass is calculated from bare copper volume

st.header("1. Coil Geometry & Derived Quantities")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Bare Cu Diameter", f"{d_cu.to(u.mm).magnitude:.3f} mm")
col2.metric("Total Wire Dia.", f"{d_total.to(u.mm).magnitude:.3f} mm")
col3.metric("Outer Radius (b)", f"{b.to(u.mm).magnitude:.2f} mm")
col4.metric("Radial Build", f"{(b - a).to(u.mm).magnitude:.2f} mm")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean Turn Length", f"{l_bar.to(u.mm).magnitude:.1f} mm")
col2.metric("Number of Turns", f"{N.to(u.dimensionless).magnitude:.0f}")
col3.metric("Wire Length", f"{total_length.to(u.m).magnitude:.0f} m")
col4.metric("Cu Wire Mass", f"{m_wire.to(u.g).magnitude:.0f} g")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Current", f"{I.to(u.A).magnitude:.3f} A")
col2.metric("Peak Power", f"{P.magnitude:.1f} W")
col3.metric("Peak Current Density (j)", f"{j.to(u.A/u.mm**2).magnitude:.2f} A/mm²")
col4.metric("Ampere-Turns (NI)", f"{NI.to(u.A).magnitude:.0f} AT")


# --- 2. SPOOL & COIL VISUALIZATION ---
st.header("2. Spool & Coil Geometry Visualization")

fig_geom, ax_geom = plt.subplots(figsize=(8, 5))

L_mm = L.to(u.mm).magnitude
a_mm = a.to(u.mm).magnitude
b_mm = b.to(u.mm).magnitude

# Assume a standard bobbin/spool thickness for visualization purposes
t_bobbin = 2.0  # mm

# --- Plot Bobbin/Spool ---
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

# --- Plot Coil Winding ---
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2, a_mm), L_mm, b_mm - a_mm, facecolor='peru', hatch='///', edgecolor='black', label='Copper Winding'))
ax_geom.add_patch(mpl.patches.Rectangle((-L_mm/2, -b_mm), L_mm, b_mm - a_mm, facecolor='peru', hatch='///', edgecolor='black'))

# Center Axis
ax_geom.axhline(0, color='black', linestyle='-.', linewidth=1, label='Center Axis')

# Labels and Styling
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


# --- BALL & MAGNETIC FIELD FUNCTIONS ---
def log_mean(rad_a, rad_b):
    return (rad_b - rad_a) / np.log(rad_b / rad_a)

def B_z(z, R, L, N, I):
    """On-axis magnetic field of a finite solenoid."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    z_plus = z + L / 2
    z_minus = z - L / 2
    term_plus = z_plus / np.sqrt(R**2 + z_plus**2)
    term_minus = z_minus / np.sqrt(R**2 + z_minus**2)
    return (mu_0 * N / L * I / 2) * (term_plus - term_minus)

def dBz_dz(z, R, L, N, I):
    """Derivative of on-axis field with respect to z."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    z_plus = z + L / 2
    z_minus = z - L / 2
    term_plus = R**2 / (R**2 + z_plus**2)**1.5
    term_minus = R**2 / (R**2 + z_minus**2)**1.5
    return (mu_0 * N / L * I / 2) * (term_plus - term_minus)

def F_z(z, R, L, N, I, r_ball):
    """Axial force on an iron sphere (mu_r >> 1)."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    V_ball = (4 / 3) * np.pi * r_ball**3
    B = B_z(z, R, L, N, I)
    dB = dBz_dz(z, R, L, N, I)
    return (3 * V_ball / (2 * mu_0)) * B * dB

def work_on_ball(z_0, r_ball, R, L, N, I):
    """Work done on iron ball when field switches on at z_0 - r_ball and off at z_0 + r_ball."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    V_ball = (4 / 3) * np.pi * r_ball**3
    z1 = z_0 - r_ball  # field turns on
    z2 = z_0 + r_ball  # field turns off
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

st.header("3. Iron Ball & Switch Configuration")
col1, col2, col3 = st.columns(3)
col1.metric("Ball Volume", f"{V_ball.to(u.mm**3).magnitude:.0f} mm³")
col2.metric("Ball Mass", f"{m_ball.to(u.g).magnitude:.2f} g")
col3.metric("B at Center", f"{B_0.to(u.mT).magnitude:.1f} mT")

col1, col2, col3 = st.columns(3)
col1.metric("Field ON at z", f"{(z_0 - r_ball).to(u.mm).magnitude:.1f} mm")
col2.metric("Field OFF at z", f"{(z_0 + r_ball).to(u.mm).magnitude:.1f} mm")
col3.metric("Work done on ball", f"{W.to(u.mJ).magnitude:.2f} mJ")

col1, col2, col3 = st.columns(3)
col1.metric("Initial Velocity", f"{v_0.to(u.mm/u.s).magnitude:.0f} mm/s")
col2.metric("Final Velocity", f"{v_f.to(u.mm/u.s).magnitude:.0f} mm/s")
col3.metric("Final Velocity (km/h)", f"{v_f.to(u.km/u.h).magnitude:.2f} km/h")


# --- 4. CYCLOTRON SYSTEM & DUTY CYCLE ---
st.header("4. Cyclotron System & Duty Cycle")

# Distance ON equals the diameter of the ball because the point sensor reads from leading edge to trailing edge
dist_on_val = 2 * r_ball_val 
duty_cycle_decimal = dist_on_val / track_circ_val
duty_cycle_pct = duty_cycle_decimal * 100

P_avg = P * duty_cycle_decimal
P_sys_avg = P_avg * n_coils_val
j_rms = j * np.sqrt(duty_cycle_decimal)

col1, col2, col3 = st.columns(3)
col1.metric("Distance ON per cycle", f"{dist_on_val:.1f} mm")
col2.metric("Individual Coil Duty Cycle", f"{duty_cycle_pct:.2f} %")
col3.metric("Total System Duty Cycle", f"{duty_cycle_pct * n_coils_val:.2f} %")

col1, col2, col3 = st.columns(3)
col1.metric("RMS Current Density (j_rms)", f"{j_rms.to(u.A/u.mm**2).magnitude:.2f} A/mm²")
col2.metric("Avg Power (Per Coil)", f"{P_avg.to(u.W).magnitude:.2f} W")
col3.metric("Avg Power (All Coils Combined)", f"{P_sys_avg.to(u.W).magnitude:.2f} W")

st.info(f"💡 **Thermal Impact Analysis:** Because the {r_ball_val * 2:.1f}mm ball strictly dictates the ON time, each individual coil rests for **{100 - duty_cycle_pct:.1f}%** of the ball's lap. Notice how drastically the **RMS Current Density** drops compared to your Peak Current Density! This tells you that for continuous cyclotron operation, thermal runaway is extremely unlikely, even if you are pulsing massive amounts of Peak Power.")


# --- 5. INDUCTANCE ---
def nagaoka_coefficient(R, L):
    """Nagaoka coefficient for finite solenoid."""
    k = 2 * R / L 
    K = 1 / (1 + 0.9 * R / L - 0.02 * (R / L)**2 + 0.01 * (R / L)**3)
    return K.to(u.dimensionless).magnitude

def solenoid_inductance(N, R, L):
    """Inductance of a finite solenoid."""
    mu_0 = 4 * np.pi * 1e-7 * u.H / u.m
    K = nagaoka_coefficient(R, L)
    return mu_0 * N**2 * np.pi * R**2 * K / L

R_coil = rho * total_length / A_cu         # Resistance calculation strictly uses bare Cu
L_coil = solenoid_inductance(N, R_eff, L)
tau = L_coil / R_coil
t_on = (2 * r_ball / v_f).to(u.ms)

st.header("5. Inductance & Time Constant")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Nagaoka Coeff (K)", f"{nagaoka_coefficient(R_eff, L):.2f}")
col2.metric("Resistance", f"{R_coil.to(u.ohm).magnitude:.1f} Ω")
col3.metric("Inductance", f"{L_coil.to(u.mH).magnitude:.1f} mH")
col4.metric("Time Constant (τ)", f"{tau.to(u.ms).magnitude:.1f} ms")
st.write(f"**Estimated ON time (First kick):** {t_on.magnitude:.4f} ms")


# --- 6. MAGNETIC FIELD PLOT ---
st.header("6. On-axis Magnetic Field Profile")

# Generate data arrays for the plot
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


# --- 7. COMBINED PLOTTING ---
st.header("7. Combined Field and Force Profiles")

# Generate range from -2L to +2L for z-axis
z_vals = np.linspace(-L_val*2, L_val*2, 200) * u.mm

# Calculate B_z and F_z over the z range
B_vals = B_z(z_vals, R_eff, L, N, I).to(u.mT).magnitude
F_vals = F_z(z_vals, R_eff, L, N, I, r_ball).to(u.mN).magnitude

fig, ax1 = plt.subplots(figsize=(10, 5))

# Plot B_z
ax1.set_xlabel('Position z (mm)')
ax1.set_ylabel('Magnetic Field B_z (mT)', color='tab:blue')
ax1.plot(z_vals.magnitude, B_vals, color='tab:blue', label='B_z')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.grid(True, alpha=0.3)

# Indicate the Switch ON/OFF region
z_on_mag = (z_0 - r_ball).to(u.mm).magnitude
z_off_mag = (z_0 + r_ball).to(u.mm).magnitude
ax1.axvspan(z_on_mag, z_off_mag, color='orange', alpha=0.2, label='Coil ON Region (Work Integration)')

# Plot F_z on a secondary y-axis
ax2 = ax1.twinx()
ax2.set_ylabel('Axial Force F_z (mN)', color='tab:red')
ax2.plot(z_vals.magnitude, F_vals, color='tab:red', linestyle='--', label='F_z')
ax2.tick_params(axis='y', labelcolor='tab:red')

fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.9), bbox_transform=ax1.transAxes)
fig.tight_layout()
st.pyplot(fig)


# --- 8. SOLENOID SYSTEM CROSS-SECTION PLOT ---
st.header("8. Solenoid System Cross-Section")

fig2, ax3 = plt.subplots(figsize=(8, 5))

r_ball_mm = r_ball.to(u.mm).magnitude
z_0_mm = z_0.to(u.mm).magnitude

# Calculate switch positions for the plot
z_on = (z_0 - r_ball).to(u.mm).magnitude
z_off = (z_0 + r_ball).to(u.mm).magnitude

# Upper coil cross-section
coil_upper = mpl.patches.Rectangle(
    (-L_mm / 2, a_mm),
    L_mm,
    b_mm - a_mm,
    facecolor='orange',
    edgecolor='black',
    linewidth=1.5,
    label='Coil'
)
ax3.add_patch(coil_upper)

# Lower coil cross-section (mirror)
coil_lower = mpl.patches.Rectangle(
    (-L_mm / 2, -b_mm),
    L_mm,
    b_mm - a_mm,
    facecolor='orange',
    edgecolor='black',
    linewidth=1.5
)
ax3.add_patch(coil_lower)

# Iron ball at switch position
ball = mpl.patches.Circle(
    (z_0_mm, 0),
    r_ball_mm,
    facecolor='gray',
    edgecolor='black',
    linewidth=1.5,
    label='Iron ball'
)
ax3.add_patch(ball)

# Mark switch positions
ax3.axvline(z_on, color='g', linestyle='--', label='Field on')
ax3.axvline(z_off, color='r', linestyle='--', label='Field off')
ax3.axvline(z_0.m_as(u.mm), color='k', linestyle=':', label='Sensor')

# Axis line
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
